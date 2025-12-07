#!/usr/bin/env python3
"""
TicketJam Scraper with SQLite Database Support

A comprehensive web scraper for TicketJam (https://ticketjam.jp/) that extracts
ticket information and stores it in a SQLite database for tracking and monitoring.

Features:
- Web scraping with BeautifulSoup
- SQLite database storage for ticket tracking
- Duplicate detection and price change monitoring
- Bot functionality for automated monitoring
- JSON export compatibility

Usage:
    python ticketjam.py scrape [URL]               # Smart scrape: display if DB empty, update if DB has data
    python ticketjam.py bot [URL1] [URL2] ...       # Run bot once
    python ticketjam.py monitor [URL1] [URL2] ...   # Run continuous bot
    python ticketjam.py stats                       # Show database stats
    python ticketjam.py dump [status]             # Export database to stdout
    python ticketjam.py unposted [status]          # Show unposted tickets
    python ticketjam.py posted [ticket_id1] ...    # Mark tickets as posted
    python ticketjam.py clear                      # Clear all data from database
    python ticketjam.py delete                     # Delete database file
"""

import re
import sys
import json
import time
import sqlite3
import hashlib
import requests
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup

@dataclass
class TicketInfo:
    """Data class for ticket information with tracking capabilities"""
    title: str = ""
    event_name: str = ""
    date: str = ""
    time: str = ""
    venue: str = ""
    location: str = ""
    price: str = ""
    quantity: str = ""
    seat_info: str = ""
    description: str = ""
    days_remaining: str = ""
    is_instant_buy: bool = False
    url: str = ""
    
    # Database tracking fields
    ticket_id: str = ""  # Unique identifier for the ticket
    first_seen: str = ""  # When this ticket was first discovered
    last_seen: str = ""   # When this ticket was last seen
    status: str = "active"  # active, sold (removed tickets are deleted)
    
    def __post_init__(self):
        """Set timestamps"""
        current_time = datetime.now().isoformat()
        if not self.first_seen:
            self.first_seen = current_time
        if not self.last_seen:
            self.last_seen = current_time

    def generate_ticket_id(self):
        """Generate unique ticket ID from URL"""
        if not self.ticket_id and self.url:
            # Extract the unique ID from the URL
            # URL format: https://ticketjam.jp/ticket/live_domestic/7938150-2511
            # Extract the last part after the final slash
            url_parts = self.url.rstrip('/').split('/')
            if url_parts:
                self.ticket_id = url_parts[-1]
            else:
                # Fallback to full URL if parsing fails
                self.ticket_id = self.url

class TicketDatabase:
    """Database manager for ticket tracking"""
    
    def __init__(self, db_path: str = "ticketjam.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create tickets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id TEXT PRIMARY KEY,
                    title TEXT,
                    event_name TEXT,
                    date TEXT,
                    time TEXT,
                    venue TEXT,
                    location TEXT,
                    price TEXT,
                    quantity TEXT,
                    seat_info TEXT,
                    description TEXT,
                    days_remaining TEXT,
                    is_instant_buy BOOLEAN,
                    url TEXT,
                    first_seen TEXT,
                    last_seen TEXT,
                    status TEXT DEFAULT 'active',
                    posted BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Add posted column to existing tables if it doesn't exist
            try:
                cursor.execute('ALTER TABLE tickets ADD COLUMN posted BOOLEAN DEFAULT 0')
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            # Create price history table for tracking price changes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT,
                    price TEXT,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticket_id) REFERENCES tickets (ticket_id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_event_name ON tickets (event_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_date ON tickets (date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets (status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_first_seen ON tickets (first_seen)')
            
            conn.commit()

    def insert_or_update_ticket(self, ticket: TicketInfo) -> tuple[bool, str]:
        """
        Insert new ticket or update existing one
        Returns: (is_new, action_taken)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if ticket already exists
            cursor.execute('SELECT ticket_id, price, status FROM tickets WHERE ticket_id = ?', (ticket.ticket_id,))
            existing = cursor.fetchone()

            current_time = datetime.now().isoformat()

            if existing:
                existing_id, existing_price, existing_status = existing

                # Update last_seen timestamp
                ticket.last_seen = current_time

                # Check if price changed
                price_changed = existing_price != ticket.price
                if price_changed:
                    # Record price change
                    cursor.execute('''
                        INSERT INTO price_history (ticket_id, price)
                        VALUES (?, ?)
                    ''', (ticket.ticket_id, ticket.price))

                    action = f"Price changed from {existing_price} to {ticket.price}"
                else:
                    action = "Updated last_seen"

                # Update the ticket
                # If price changed, set posted to false to trigger re-posting
                if price_changed:
                    cursor.execute('''
                        UPDATE tickets SET
                            title = ?, event_name = ?, date = ?, time = ?, venue = ?, location = ?,
                            price = ?, quantity = ?, seat_info = ?, description = ?, days_remaining = ?,
                            is_instant_buy = ?, url = ?, last_seen = ?, status = ?, posted = 0,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE ticket_id = ?
                    ''', (
                        ticket.title, ticket.event_name, ticket.date, ticket.time, ticket.venue,
                        ticket.location, ticket.price, ticket.quantity, ticket.seat_info,
                        ticket.description, ticket.days_remaining, ticket.is_instant_buy,
                        ticket.url, ticket.last_seen, ticket.status, ticket.ticket_id
                    ))
                else:
                    cursor.execute('''
                        UPDATE tickets SET
                            title = ?, event_name = ?, date = ?, time = ?, venue = ?, location = ?,
                            price = ?, quantity = ?, seat_info = ?, description = ?, days_remaining = ?,
                            is_instant_buy = ?, url = ?, last_seen = ?, status = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE ticket_id = ?
                    ''', (
                        ticket.title, ticket.event_name, ticket.date, ticket.time, ticket.venue,
                        ticket.location, ticket.price, ticket.quantity, ticket.seat_info,
                        ticket.description, ticket.days_remaining, ticket.is_instant_buy,
                        ticket.url, ticket.last_seen, ticket.status, ticket.ticket_id
                    ))

                conn.commit()
                return False, action

            else:
                # Insert new ticket
                ticket.first_seen = current_time
                ticket.last_seen = current_time

                cursor.execute('''
                    INSERT INTO tickets (
                        ticket_id, title, event_name, date, time, venue, location, price,
                        quantity, seat_info, description, days_remaining, is_instant_buy, url,
                        first_seen, last_seen, status, posted
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ticket.ticket_id, ticket.title, ticket.event_name, ticket.date, ticket.time,
                    ticket.venue, ticket.location, ticket.price, ticket.quantity,
                    ticket.seat_info, ticket.description, ticket.days_remaining,
                    ticket.is_instant_buy, ticket.url, ticket.first_seen, ticket.last_seen, ticket.status, 0
                ))

                # Record initial price
                cursor.execute('''
                    INSERT INTO price_history (ticket_id, price)
                    VALUES (?, ?)
                ''', (ticket.ticket_id, ticket.price))

                conn.commit()
                return True, "New ticket added"

    def delete_removed_tickets(self, current_ticket_ids: List[str]):
        """Delete tickets not in current scrape (they're no longer available)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if current_ticket_ids:
                placeholders = ','.join(['?' for _ in current_ticket_ids])
                cursor.execute(f'''
                    DELETE FROM tickets
                    WHERE status = 'active' AND ticket_id NOT IN ({placeholders})
                ''', current_ticket_ids)
            else:
                # If no current tickets, delete all active tickets
                cursor.execute('''
                    DELETE FROM tickets
                    WHERE status = 'active'
                ''')

            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            stats = {}

            # Total tickets by status
            cursor.execute('SELECT status, COUNT(*) FROM tickets GROUP BY status')
            stats['by_status'] = dict(cursor.fetchall())

            # Tickets by event
            cursor.execute('''
                SELECT event_name, COUNT(*) as count
                FROM tickets
                WHERE status = 'active'
                GROUP BY event_name
                ORDER BY count DESC
            ''')
            stats['by_event'] = dict(cursor.fetchall())

            return stats

    def dump_tickets_to_json(self, status_filter: str = None) -> Dict:
        """
        Export all tickets from database to JSON format and output to stdout

        Args:
            status_filter: Filter by status ('active', 'sold') or None for all

        Returns:
            Dictionary containing all ticket data
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Build query based on filter
            if status_filter:
                query = 'SELECT * FROM tickets WHERE status = ? ORDER BY first_seen DESC'
                cursor.execute(query, (status_filter,))
            else:
                query = 'SELECT * FROM tickets ORDER BY first_seen DESC'
                cursor.execute(query)

            # Get column names
            columns = [description[0] for description in cursor.description]

            # Fetch all tickets
            tickets_data = []
            for row in cursor.fetchall():
                ticket_dict = dict(zip(columns, row))
                tickets_data.append(ticket_dict)

            # Get price history for each ticket
            for ticket in tickets_data:
                cursor.execute('''
                    SELECT price, recorded_at
                    FROM price_history
                    WHERE ticket_id = ?
                    ORDER BY recorded_at
                ''', (ticket['ticket_id'],))

                price_history = []
                for price, recorded_at in cursor.fetchall():
                    price_history.append({
                        'price': price,
                        'recorded_at': recorded_at
                    })

                ticket['price_history'] = price_history

            # Create export data structure
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_tickets': len(tickets_data),
                'status_filter': status_filter,
                'database_path': self.db_path,
                'tickets': tickets_data
            }

            # Output JSON to stdout
            print(json.dumps(export_data, ensure_ascii=False, indent=2))

            return export_data

    def clear_database(self) -> bool:
        """
        Clear all data from the database (keeps table structure)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Clear all data from tables
                cursor.execute("DELETE FROM price_history")
                cursor.execute("DELETE FROM tickets")
                conn.commit()

                return True

        except Exception as e:
            print(f"Error clearing database: {e}", file=sys.stderr)
            return False

    def delete_database(self) -> bool:
        """
        Delete the entire database file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Delete the database file
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                print(f"Database file '{self.db_path}' deleted successfully", file=sys.stderr)
            else:
                print(f"Database file '{self.db_path}' does not exist", file=sys.stderr)

            return True

        except Exception as e:
            print(f"Error deleting database: {e}", file=sys.stderr)
            return False

    def get_unposted_tickets(self, status_filter: str = None) -> List[Dict]:
        """
        Get all tickets that haven't been posted yet

        Args:
            status_filter: Optional status filter ('active', 'sold')

        Returns:
            List of ticket dictionaries that need to be posted
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Build query based on status filter
                if status_filter:
                    if status_filter not in ['active', 'sold']:
                        print(f"Invalid status filter: {status_filter}", file=sys.stderr)
                        print("Valid options: active, sold or leave empty for all", file=sys.stderr)
                        return []

                    cursor.execute('''
                        SELECT * FROM tickets
                        WHERE posted = 0 AND status = ?
                        ORDER BY created_at DESC
                    ''', (status_filter,))
                else:
                    cursor.execute('''
                        SELECT * FROM tickets
                        WHERE posted = 0
                        ORDER BY created_at DESC
                    ''')

                tickets = []
                for row in cursor.fetchall():
                    ticket_dict = {
                        'ticket_id': row[0],
                        'title': row[1],
                        'event_name': row[2],
                        'date': row[3],
                        'time': row[4],
                        'venue': row[5],
                        'location': row[6],
                        'price': row[7],
                        'quantity': row[8],
                        'seat_info': row[9],
                        'description': row[10],
                        'days_remaining': row[11],
                        'is_instant_buy': bool(row[12]),
                        'url': row[13],
                        'first_seen': row[14],
                        'last_seen': row[15],
                        'status': row[16],
                        'created_at': row[17],
                        'updated_at': row[18],
                        'posted': bool(row[19])
                    }
                    tickets.append(ticket_dict)

                return tickets

        except Exception as e:
            print(f"Error getting unposted tickets: {e}", file=sys.stderr)
            return []

    def get_price_history(self, ticket_id: str) -> List[Dict]:
        """
        Get price history for a specific ticket

        Args:
            ticket_id: The ticket ID to get price history for

        Returns:
            List of price history entries with price and recorded_at
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT price, recorded_at
                    FROM price_history
                    WHERE ticket_id = ?
                    ORDER BY recorded_at
                ''', (ticket_id,))

                price_history = []
                for price, recorded_at in cursor.fetchall():
                    price_history.append({
                        'price': price,
                        'recorded_at': recorded_at
                    })

                return price_history
        except Exception as e:
            print(f"Error getting price history for {ticket_id}: {e}", file=sys.stderr)
            return []

    def format_price_change_info(self, current_price: str, price_history: List[Dict]) -> str:
        """
        Format price change information for display

        Args:
            current_price: Current price string
            price_history: List of price history entries

        Returns:
            Formatted price string with change information
        """
        if len(price_history) <= 1:
            return current_price  # No price changes

        # Get previous price (second to last entry)
        previous_price = price_history[-2]['price']

        if previous_price == current_price:
            return current_price  # No change

        # Parse prices for comparison
        try:
            current_val = int(current_price.replace(',', '').replace('円', ''))
            previous_val = int(previous_price.replace(',', '').replace('円', ''))

            if current_val > previous_val:
                # Price increased
                diff = current_val - previous_val
                return f"{current_price} 📈 (+{diff:,}円)\n~~{previous_price}~~"
            else:
                # Price decreased
                diff = previous_val - current_val
                return f"{current_price} 📉 (-{diff:,}円)\n~~{previous_price}~~"
        except (ValueError, AttributeError):
            # Fallback if price parsing fails
            return f"{current_price}\n前回: {previous_price}"

    def get_ticket_with_price_info(self, ticket_dict: Dict) -> Dict:
        """
        Enhance ticket dictionary with price change information

        Args:
            ticket_dict: Basic ticket dictionary

        Returns:
            Enhanced ticket dictionary with price_info and color_hint
        """
        price_history = self.get_price_history(ticket_dict['ticket_id'])
        price_info = self.format_price_change_info(ticket_dict['price'], price_history)

        # Determine color hint based on price change
        color_hint = 'default'  # green
        if len(price_history) > 1:
            try:
                current_val = int(ticket_dict['price'].replace(',', '').replace('円', ''))
                previous_val = int(price_history[-2]['price'].replace(',', '').replace('円', ''))
                if current_val > previous_val:
                    color_hint = 'increase'  # red
                elif current_val < previous_val:
                    color_hint = 'decrease'  # bright green
            except (ValueError, AttributeError, IndexError):
                pass

        # Add enhanced information to ticket
        enhanced_ticket = ticket_dict.copy()
        enhanced_ticket['price_info'] = price_info
        enhanced_ticket['color_hint'] = color_hint
        enhanced_ticket['price_history'] = price_history

        return enhanced_ticket

    def mark_tickets_as_posted(self, ticket_ids: List[str]) -> bool:
        """
        Mark tickets as posted

        Args:
            ticket_ids: List of ticket IDs to mark as posted

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Update posted status for specified tickets
                placeholders = ','.join(['?' for _ in ticket_ids])
                cursor.execute(f'''
                    UPDATE tickets
                    SET posted = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE ticket_id IN ({placeholders})
                ''', ticket_ids)

                updated_count = cursor.rowcount
                conn.commit()

                print(f"Marked {updated_count} tickets as posted", file=sys.stderr)
                return True

        except Exception as e:
            print(f"Error marking tickets as posted: {e}", file=sys.stderr)
            return False

    def mark_ticket_as_posted(self, ticket_id: str) -> bool:
        """
        Mark a single ticket as posted

        Args:
            ticket_id: Ticket ID to mark as posted

        Returns:
            bool: True if successful, False otherwise
        """
        return self.mark_tickets_as_posted([ticket_id])

    def is_database_empty(self) -> bool:
        """
        Check if the database is empty (no tickets)

        Returns:
            bool: True if database is empty, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM tickets')
                count = cursor.fetchone()[0]
                return count == 0
        except Exception as e:
            print(f"Error checking database: {e}", file=sys.stderr)
            return True  # Assume empty if error

class TicketJamScraper:
    """Scraper for TicketJam website with database integration"""

    def __init__(self, db_path: str = "ticketjam.db"):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.db = TicketDatabase(db_path)

    def scrape_tickets(self, url: str) -> List[TicketInfo]:
        """Scrape tickets from TicketJam URL using direct HTML element extraction"""
        try:
            print(f"Fetching URL: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            tickets = []



            # Strategy 1: Find ticket cards/containers by common patterns
            ticket_containers = []

            # Look for elements that contain price information (including li elements for TicketJam)
            for element in soup.find_all(['div', 'article', 'section', 'li']):
                if self._contains_ticket_data(element):
                    ticket_containers.append(element)

            # Strategy 2: If no containers found, look for elements containing price patterns
            if not ticket_containers:
                # Find all elements that contain price patterns in their text
                all_elements = soup.find_all(['div', 'span', 'p', 'article', 'section', 'li'])
                price_elements = []

                for elem in all_elements:
                    elem_text = elem.get_text()
                    if re.search(r'\d{1,3}(?:,\d{3})*[\s\n]*円', elem_text):
                        price_elements.append(elem)

                for price_elem in price_elements:
                    container = price_elem
                    # Walk up the DOM to find a reasonable container
                    for level in range(5):  # Max 5 levels up
                        if container and container.name != 'body':
                            if self._contains_ticket_data(container):
                                ticket_containers.append(container)
                                break
                            container = container.parent
                        else:
                            break

            # Extract ticket data from each container
            for container in ticket_containers:
                try:
                    ticket = self._extract_ticket_from_element(container)
                    if ticket and self._is_valid_ticket(ticket):
                        tickets.append(ticket)
                except Exception as e:
                    continue

            # Remove duplicates based on ticket_id
            unique_tickets = []
            seen_ids = set()
            id_counts = {}

            for ticket in tickets:
                # Count how many times each ID appears
                id_counts[ticket.ticket_id] = id_counts.get(ticket.ticket_id, 0) + 1

                if ticket.ticket_id not in seen_ids:
                    unique_tickets.append(ticket)
                    seen_ids.add(ticket.ticket_id)

            print(f"Found {len(unique_tickets)} unique tickets")
            return unique_tickets

        except requests.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            return []

    def _contains_ticket_data(self, element) -> bool:
        """Check if element contains ticket data without text matching"""
        if not element or not hasattr(element, 'get_text'):
            return False

        text = element.get_text()

        # Must have price information (this is universal)
        has_price = bool(re.search(r'\d{1,3}(?:,\d{3})*[\s\n]*円', text))

        # Should be reasonably sized (not too small, not too large)
        text_length = len(text.strip())
        reasonable_size = 50 < text_length < 5000  # Increased upper limit to catch more containers

        # Should have some structure (multiple lines or sections)
        has_structure = len(text.split('\n')) > 3 or len(text.split()) > 10

        return has_price and reasonable_size and has_structure

    def _extract_ticket_from_element(self, element) -> Optional[TicketInfo]:
        """Extract ticket information directly from HTML element"""
        try:
            ticket = TicketInfo()

            # Extract individual ticket URL
            # Check if the element itself is a link
            if element.name == 'a' and element.get('href'):
                href = element.get('href')
                if href.startswith('/'):
                    ticket.url = f"https://ticketjam.jp{href}"
                elif href.startswith('http'):
                    ticket.url = href
                else:
                    ticket.url = f"https://ticketjam.jp/{href}"
            else:
                # Look for parent link element
                parent = element.parent
                while parent and parent.name != 'body':
                    if parent.name == 'a' and parent.get('href'):
                        href = parent.get('href')
                        if href.startswith('/'):
                            ticket.url = f"https://ticketjam.jp{href}"
                        elif href.startswith('http'):
                            ticket.url = href
                        else:
                            ticket.url = f"https://ticketjam.jp/{href}"
                        break
                    parent = parent.parent

                # If no parent link found, look for child links
                if not ticket.url:
                    ticket_links = element.find_all('a', href=True)
                    for link in ticket_links:
                        href = link.get('href')
                        if href and ('/tickets/' in href or '/ticket/' in href):
                            if href.startswith('/'):
                                ticket.url = f"https://ticketjam.jp{href}"
                            elif href.startswith('http'):
                                ticket.url = href
                            else:
                                ticket.url = f"https://ticketjam.jp/{href}"
                            break

            # Get all text content
            full_text = element.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]



            # Extract price from full text (handles multi-line prices)
            price_patterns = [
                r'(\d{1,3}(?:,\d{3})*)[\s\n]*円(?:/枚)?',  # With optional /枚
                r'(\d{1,3}(?:,\d{3})*)[\s\n]+円',          # With whitespace
                r'(\d{1,3}(?:,\d{3})*)\s*円',              # Simple format
            ]

            for pattern in price_patterns:
                price_match = re.search(pattern, full_text)
                if price_match and not ticket.price:
                    ticket.price = price_match.group(1) + '円'
                    break

            # Extract other patterns from lines
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Extract quantity (universal pattern)
                quantity_match = re.search(r'(\d+)\s*枚', line)
                if quantity_match and not ticket.quantity:
                    ticket.quantity = quantity_match.group(1) + '枚'

                # Extract date (universal pattern)
                date_match = re.search(r'(\d{2,4})[/\-年](\d{1,2})[/\-月](\d{1,2})', line)
                if date_match and not ticket.date:
                    year, month, day = date_match.groups()
                    if len(year) == 2:
                        year = '20' + year
                    ticket.date = f"{year}/{month.zfill(2)}/{day.zfill(2)}"

                # Extract time (universal pattern)
                time_match = re.search(r'(\d{1,2}):(\d{2})', line)
                if time_match and not ticket.time:
                    ticket.time = f"{time_match.group(1)}:{time_match.group(2)}"

                # Extract remaining days
                days_match = re.search(r'残り\s*(\d+)\s*日', line)
                if days_match and not ticket.days_remaining:
                    ticket.days_remaining = f"残り{days_match.group(1)}日"



                # Check for instant buy
                if '即決' in line:
                    ticket.is_instant_buy = True

            # Extract event name (first substantial line that's not price/date/time)
            for line in lines[:5]:  # Check first few lines
                if (len(line) > 10 and
                    not re.search(r'\d{1,3}(?:,\d{3})*\s*円', line) and
                    not re.search(r'\d{1,2}:\d{2}', line) and
                    not re.search(r'\d+\s*枚', line) and
                    not ticket.event_name):
                    ticket.event_name = line
                    break

            # Set title as event name
            ticket.title = ticket.event_name

            # Extract venue and location from date/time lines
            for line in lines:
                # Look for the specific pattern: date(day) time location venue
                # Example: "2025/12/23(火) 19:00 東京 ガーデンシアター"
                venue_location_match = re.search(r'\d{4}/\d{1,2}/\d{1,2}\([^)]+\)\s+\d{1,2}:\d{2}\s+([^\s]+)\s+(.+)', line)
                if venue_location_match:
                    ticket.location = venue_location_match.group(1).strip()
                    ticket.venue = venue_location_match.group(2).strip()
                    break

                # Alternative pattern without day of week
                # Example: "2026/01/04 13:30 千葉 幕張メッセ"
                venue_location_match2 = re.search(r'\d{4}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}\s+([^\s]+)\s+(.+)', line)
                if venue_location_match2:
                    ticket.location = venue_location_match2.group(1).strip()
                    ticket.venue = venue_location_match2.group(2).strip()
                    break

            # Store full description (first 500 chars)
            ticket.description = full_text[:500] if full_text else ""

            # Generate unique ticket ID after all fields are populated
            ticket.generate_ticket_id()

            return ticket if ticket.price else None

        except Exception as e:
            print(f"Error extracting ticket: {e}")
            return None

    def _is_valid_ticket(self, ticket: TicketInfo) -> bool:
        """Validate that ticket has minimum required data"""
        return bool(ticket.price and (ticket.event_name or ticket.description))

    def scrape_and_update_database(self, url: str) -> Dict[str, Any]:
        """
        Scrape tickets and update database, returning summary of changes
        """
        print(f"Scraping and updating database from: {url}")

        # Scrape current tickets
        tickets = self.scrape_tickets(url)

        if not tickets:
            return {
                'success': False,
                'message': 'No tickets found',
                'new_tickets': 0,
                'updated_tickets': 0,
                'deleted_tickets': 0,
                'price_changes': 0
            }

        # Update database
        new_count = 0
        updated_count = 0
        new_tickets = []
        price_changes = []

        current_ticket_ids = []

        for ticket in tickets:
            is_new, action = self.db.insert_or_update_ticket(ticket)
            current_ticket_ids.append(ticket.ticket_id)

            if is_new:
                new_count += 1
                new_tickets.append(ticket)
            elif "Price changed" in action:
                # Only count as updated if something actually changed (price change)
                updated_count += 1
                price_changes.append((ticket, action))
            # If action is just "Updated last_seen", don't count as updated

        # Delete missing tickets (they're no longer available)
        removed_count = self.db.delete_removed_tickets(current_ticket_ids)

        # Prepare summary
        summary = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'total_scraped': len(tickets),
            'new_tickets': new_count,
            'updated_tickets': updated_count,
            'deleted_tickets': removed_count,
            'price_changes': len(price_changes),
            'new_ticket_details': [
                {
                    'event': t.event_name,
                    'date': t.date,
                    'price': t.price,
                    'venue': t.venue
                } for t in new_tickets
            ]
        }

        return summary

def create_ticket_bot(urls: List[str], db_path: str = "ticketjam.db"):
    """Create a ticket monitoring bot"""
    scraper = TicketJamScraper(db_path)

    def run_bot_check():
        """Run a single bot check cycle"""
        print(f"\n=== Bot Check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")

        total_new = 0
        total_price_changes = 0

        for url in urls:
            try:
                summary = scraper.scrape_and_update_database(url)

                if summary['success']:
                    total_new += summary['new_tickets']
                    total_price_changes += summary['price_changes']

                    print(f"URL: {url}")
                    print(f"  New tickets: {summary['new_tickets']}")
                    print(f"  Updated: {summary['updated_tickets']}")
                    print(f"  Deleted: {summary['deleted_tickets']}")

                    # Show new tickets
                    if summary['new_ticket_details']:
                        print("  New tickets found:")
                        for ticket in summary['new_ticket_details']:
                            print(f"    - {ticket['event']} | {ticket['date']} | {ticket['price']} | {ticket['venue']}")

                time.sleep(2)  # Be respectful between requests

            except Exception as e:
                print(f"Error processing {url}: {e}")

        print(f"\n=== Summary ===")
        print(f"Total new tickets: {total_new}")
        print(f"Total price changes: {total_price_changes}")

        return total_new, total_price_changes

    return run_bot_check

def run_continuous_bot(urls: List[str], db_path: str = "ticketjam.db", check_interval: int = 300):
    """Run the bot continuously with specified interval"""
    bot_check = create_ticket_bot(urls, db_path)

    print(f"Starting continuous bot monitoring...")
    print(f"URLs to monitor: {len(urls)}")
    print(f"Check interval: {check_interval} seconds")
    print("Press Ctrl+C to stop")

    try:
        while True:
            bot_check()
            print(f"Sleeping for {check_interval} seconds...")
            time.sleep(check_interval)
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Bot error: {e}")

def get_bot_notifications(db_path: str = "ticketjam.db", since_minutes: int = 60) -> Dict[str, List]:
    """
    Get notifications for new tickets and price changes

    Args:
        db_path: Database file path
        since_minutes: Look for changes in the last N minutes

    Returns:
        Dictionary with new tickets and price changes
    """
    db = TicketDatabase(db_path)
    since_time = datetime.now().replace(minute=max(0, datetime.now().minute - since_minutes)).isoformat()

    # Get new tickets
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM tickets
            WHERE first_seen > ? AND status = 'active'
            ORDER BY first_seen DESC
        ''', (since_time,))

        columns = [description[0] for description in cursor.description]
        new_tickets = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Get price changes (simplified for now)
    price_changes = []

    return {
        'new_tickets': new_tickets,
        'price_changes': price_changes,
        'since_time': since_time
    }

def scrape_ticketjam_url(url: str) -> List[TicketInfo]:
    """Convenience function to scrape a TicketJam URL"""
    scraper = TicketJamScraper()
    tickets = scraper.scrape_tickets(url)
    return tickets


def dump_database_to_json(status_filter: str = None) -> Dict:
    """
    Convenience function to export database to JSON and output to stdout

    Args:
        status_filter: Filter by status ('active', 'sold') or None for all

    Returns:
        Dictionary containing all ticket data
    """
    db = TicketDatabase()
    return db.dump_tickets_to_json(status_filter)


def clear_database() -> bool:
    """
    Convenience function to clear all data from the database

    Returns:
        bool: True if successful, False otherwise
    """
    db = TicketDatabase()
    return db.clear_database()


def delete_database() -> bool:
    """
    Convenience function to delete the database file

    Returns:
        bool: True if successful, False otherwise
    """
    db = TicketDatabase()
    return db.delete_database()


def get_unposted_tickets(status_filter: str = None) -> List[Dict]:
    """
    Convenience function to get unposted tickets

    Args:
        status_filter: Optional status filter ('active', 'sold')

    Returns:
        List of ticket dictionaries that need to be posted
    """
    db = TicketDatabase()
    return db.get_unposted_tickets(status_filter)


def mark_tickets_as_posted(ticket_ids: List[str]) -> bool:
    """
    Convenience function to mark tickets as posted

    Args:
        ticket_ids: List of ticket IDs to mark as posted

    Returns:
        bool: True if successful, False otherwise
    """
    db = TicketDatabase()
    return db.mark_tickets_as_posted(ticket_ids)


def mark_ticket_as_posted(ticket_id: str) -> bool:
    """
    Convenience function to mark a single ticket as posted

    Args:
        ticket_id: Ticket ID to mark as posted

    Returns:
        bool: True if successful, False otherwise
    """
    db = TicketDatabase()
    return db.mark_ticket_as_posted(ticket_id)


def main():
    """Main function with multiple modes"""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python ticketjam.py scrape [URL]               # Smart scrape: display if DB empty, update if DB has data")
        print("  python ticketjam.py bot [URL1] [URL2] ...       # Run bot once")
        print("  python ticketjam.py monitor [URL1] [URL2] ...   # Run continuous bot")
        print("  python ticketjam.py stats                       # Show database stats")
        print("  python ticketjam.py dump [status]             # Export database to stdout")
        print("  python ticketjam.py unposted [status]          # Show unposted tickets")
        print("  python ticketjam.py posted [ticket_id1] ...    # Mark tickets as posted")
        print("  python ticketjam.py clear                      # Clear all data from database")
        print("  python ticketjam.py delete                     # Delete database file")
        return

    mode = sys.argv[1].lower()

    if mode == "scrape":
        # Intelligent scrape: display-only if DB empty, update if DB has data
        default_url = "https://ticketjam.jp/tickets/zuttomayonakade-iinoni?sort_query%5BisSellable%5D=true"
        url = sys.argv[2] if len(sys.argv) > 2 else default_url

        # Check if database is empty to determine behavior
        db = TicketDatabase()
        is_empty = db.is_database_empty()

        if is_empty:
            # Database is empty - first run: scrape and store
            scraper = TicketJamScraper()
            summary = scraper.scrape_and_update_database(url)

            print(f"\nFirst scrape completed - tickets stored in database:")
            print(f"  New tickets: {summary['new_tickets']}")
            print(f"  Updated tickets: {summary['updated_tickets']}")
            print(f"  Deleted tickets: {summary['deleted_tickets']}")
            print(f"  Price changes: {summary['price_changes']}")

            # Also display sample tickets for user feedback
            if summary['new_tickets'] > 0:
                print(f"\nSample of {min(5, summary['new_tickets'])} tickets added:")
                tickets = scrape_ticketjam_url(url)
                for i, ticket in enumerate(tickets[:5], 1):
                    print(f"  {i}. {ticket.title} - {ticket.price} ({ticket.quantity})")
                if len(tickets) > 5:
                    print(f"  ... and {len(tickets) - 5} more tickets")
        else:
            # Database has data - update mode
            scraper = TicketJamScraper()
            summary = scraper.scrape_and_update_database(url)

            print(f"\nScrape and update completed:")
            print(f"  New tickets: {summary['new_tickets']}")
            print(f"  Updated tickets: {summary['updated_tickets']}")
            print(f"  Deleted tickets: {summary['deleted_tickets']}")
            print(f"  Price changes: {summary['price_changes']}")

    elif mode == "bot":
        # Run bot once
        urls = sys.argv[2:] if len(sys.argv) > 2 else [
            "https://ticketjam.jp/tickets/zuttomayonakade-iinoni?sort_query%5BisSellable%5D=true"
        ]

        bot_check = create_ticket_bot(urls)
        bot_check()

    elif mode == "monitor":
        # Run continuous monitoring
        urls = sys.argv[2:] if len(sys.argv) > 2 else [
            "https://ticketjam.jp/tickets/zuttomayonakade-iinoni?sort_query%5BisSellable%5D=true"
        ]

        run_continuous_bot(urls, check_interval=300)  # 5 minutes

    elif mode == "stats":
        # Show database statistics
        db = TicketDatabase()
        stats = db.get_statistics()

        print("=== Database Statistics ===")
        print(f"Tickets by status: {stats.get('by_status', {})}")
        print(f"Active tickets by event:")
        for event, count in stats.get('by_event', {}).items():
            print(f"  {event}: {count}")

    elif mode == "dump":
        # Export database to JSON (stdout only)
        status_filter = sys.argv[2] if len(sys.argv) > 2 else None

        # Validate status filter
        valid_statuses = ['active', 'sold']
        if status_filter and status_filter not in valid_statuses:
            print(f"Invalid status filter: {status_filter}", file=sys.stderr)
            print(f"Valid options: {', '.join(valid_statuses)} or leave empty for all", file=sys.stderr)
            return

        db = TicketDatabase()
        export_data = db.dump_tickets_to_json(status_filter)

    elif mode == "clear":
        # Clear all data from database
        db = TicketDatabase()
        if db.clear_database():
            print("Database cleared successfully")
        else:
            print("Failed to clear database")

    elif mode == "delete":
        # Delete database file
        db = TicketDatabase()
        if db.delete_database():
            print("Database deleted successfully")
        else:
            print("Failed to delete database")

    elif mode == "unposted":
        # Show unposted tickets
        status_filter = sys.argv[2] if len(sys.argv) > 2 else None

        db = TicketDatabase()
        unposted_tickets = db.get_unposted_tickets(status_filter)

        if not unposted_tickets:
            print("No unposted tickets found")
        else:
            print(f"Found {len(unposted_tickets)} unposted tickets:")
            for ticket in unposted_tickets:
                posted_status = "posted" if ticket['posted'] else "unposted"
                print(f"  {ticket['ticket_id'][:8]}... - {ticket['event_name'][:40]}... - {ticket['price']} - {ticket['status']} - {posted_status}")

            # Also output as JSON for easy processing
            print("\nJSON output:")
            print(json.dumps({
                'total_unposted': len(unposted_tickets),
                'tickets': unposted_tickets
            }, ensure_ascii=False, indent=2))

    elif mode == "posted":
        # Mark tickets as posted
        if len(sys.argv) < 3:
            print("Usage: python ticketjam.py posted [ticket_id1] [ticket_id2] ...")
            return

        ticket_ids = sys.argv[2:]

        db = TicketDatabase()
        if db.mark_tickets_as_posted(ticket_ids):
            print(f"Successfully marked {len(ticket_ids)} tickets as posted")
        else:
            print("Failed to mark tickets as posted")

    else:
        print(f"Unknown mode: {mode}")

if __name__ == "__main__":
    main()
