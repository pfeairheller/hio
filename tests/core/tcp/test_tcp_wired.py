# -*- encoding: utf-8 -*-
"""
tests.core.test_tcp module

"""
import pytest

import sys
import os
import time
import socket
from collections import deque
import ssl

from hio.base import tyming
from hio.core import wiring
from hio.core.tcp.clienting import openClient, Client, ClientTls
from hio.core.tcp.serving import openServer, Server, Remoter, ServerTls


def test_tcp_service_wired():
    """
    Test Classes tcp service methods
    """
    # wire log everything to samefile
    tymist = tyming.Tymist()
    with wiring.openWL(samed=True, filed=True) as wl, \
         openServer(tymist=tymist,  ha=("", 6101), wl=wl) as server, \
         openClient(tymist=tymist,  ha=("127.0.0.1", 6101), wl=wl) as beta:

        assert isinstance(wl, wiring.WireLog)
        assert wl.rxed is True
        assert wl.txed is True
        assert wl.samed is True
        assert wl.filed is True
        assert wl.name == "test"
        assert wl.temp == True
        assert wl.rxl is wl.txl
        assert wl.opened

        assert server.opened == True
        assert server.ha == ('0.0.0.0', 6101)
        assert server.eha == ('127.0.0.1', 6101)
        assert server.wl == wl

        assert beta.opened == True
        assert beta.accepted == False
        assert beta.connected == False
        assert beta.cutoff == False
        assert beta.wl == wl

        # connect beta to server
        while not (beta.connected and beta.ca in server.ixes):
            beta.serviceConnect()
            server.serviceConnects()
            time.sleep(0.05)

        assert beta.accepted == True
        assert beta.connected == True
        assert beta.cutoff == False
        assert beta.ca == beta.cs.getsockname()
        assert beta.ha == beta.cs.getpeername() == server.eha

        ixBeta = server.ixes[beta.ca]
        assert ixBeta.cs.getsockname() == beta.cs.getpeername()
        assert ixBeta.cs.getpeername() == beta.cs.getsockname()
        assert ixBeta.ca == beta.ca
        assert ixBeta.ha == beta.ha

        msgOut1 = b"Beta sends to Server first"
        beta.tx(msgOut1)
        while not ixBeta.rxbs and beta.txbs:
            beta.serviceSends()
            time.sleep(0.05)
            server.serviceReceivesAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        assert msgIn == msgOut1
        offset = len(ixBeta.rxbs)  # offset into .rxbs of first message

        # send multiple additional messages
        msgOut2 = b"Beta sends to Server second"
        beta.tx(msgOut2)
        msgOut3 = b"Beta sends to Server third"
        beta.tx(msgOut3)
        while len(ixBeta.rxbs) < len(msgOut1) + len(msgOut2) + len(msgOut3):
            beta.serviceSends()
            server.serviceReceivesAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        assert msgIn == msgOut1 + msgOut2 + msgOut3
        ixBeta.clearRxbs()  # clear out the receive buffer

        # build message too big to fit in buffer
        size = beta.actualBufSizes()[0]
        msgOutBig = bytearray()
        count = 0
        while (len(msgOutBig) <= size * 4):
            msgOutBig.extend(b"%032x_" % (count))
            count += 1
        assert len(msgOutBig) >= size * 4

        beta.tx(msgOutBig)
        while len(ixBeta.rxbs) < len(msgOutBig):
            beta.serviceSends()
            time.sleep(0.05)
            server.serviceReceivesAllIx()
            time.sleep(0.05)
        msgIn = bytes(ixBeta.rxbs)
        ixBeta.clearRxbs()
        assert msgIn == msgOutBig

        # send from server to beta
        msgOut = b"Server sends to Beta"
        ixBeta.tx(msgOut)
        while len(beta.rxbs) < len(msgOut):
            server.serviceSendsAllIx()
            beta.serviceReceives()
            time.sleep(0.05)
        msgIn = bytes(beta.rxbs)
        beta.clearRxbs()
        assert msgIn == msgOut

        # send big from server to beta
        ixBeta.tx(msgOutBig)
        while len(beta.rxbs) < len(msgOutBig):
            server.serviceSendsAllIx()
            time.sleep(0.05)
            beta.serviceReceives()
            time.sleep(0.05)
        msgIn = bytes(beta.rxbs)
        beta.clearRxbs()
        assert msgIn == msgOutBig

        assert wl.readRx() == (b'')
        assert wl.readTx() == (b'')

    assert beta.opened == False
    assert server.opened == False
    assert wl.rxl.closed
    assert wl.txl.closed
    assert not wl.opened
    assert not os.path.exists(wl.dirPath)


    """Done Test"""



if __name__ == "__main__":
    test_tcp_service_wired()
