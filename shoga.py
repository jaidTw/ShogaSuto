import random

SHOGAS = [
    "9IWEk8L.jpeg",
    "2srC5pK.jpeg",
    "EAoNwt8.jpeg",
    "KFhTent.jpeg",
    "U93uNN4.jpeg",
    "KWxyEG5.jpeg",
    "gvRYA2w.jpeg",
    "2ABZNVY.jpeg",
    "iREJ6Ca.jpeg",
    "rXc4DYR.jpeg",
    "TCIt6oz.jpeg",
    "QRW4xRT.jpeg",
    "nCrPZ3n.jpeg",
    "tblGHzp.jpeg",
    "B60botb.jpeg",
    "FLHV3NA.jpeg",
    "wKiihAB.png",
    "vdgtAbz.jpeg",
    "TcY3vmW.jpeg",
    "PnrBBCB.jpeg",
    "6IbFzkG.jpeg",
    "XLp2uLH.jpeg",
    "sUAanSs.jpeg",
    "UpP1lXx.jpeg",
    "8GdLd4q.png",
    "DQyMteu.png",
    "EwORQr6.png",
    "vRNRPTh.png",
    "w7d2evH.png",
    "mYGfV3c.png",
    "A6jvz5g.png",
    "ESPvbAA.png",
    "0rGKLaF.png",
    "rzU4YDM.png",
]

NAILONGS = [
    "53NIvAc.jpeg",
    "9jwwono.jpeg",
    "eK6EGGd.jpeg",
    "ALlZD5v.png",
    "bdtqs1h.jpeg",
    "bClHZyn.jpeg",
]

def random_shoga():
    if random.randint(0, 99) < 2:
        fname = random.choice(NAILONGS)
    else:
        fname = random.choice(SHOGAS)

    return f"https://i.imgur.com/{fname}"

