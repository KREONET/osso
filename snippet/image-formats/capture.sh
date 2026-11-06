#!/bin/bash
# 책 1.2절(디스크 이미지 형식)의 출력을 다시 받는 스크립트.
# 클라우드 이미지와 변환 결과로 5 GB 가까이 쓰므로 여유 있는 디스크에서 실행한다.
#
#   mkdir -p ~/osso-work
#   docker run --rm -v ~/osso-work:/work -v "$PWD/snippet/image-formats/capture.sh:/c.sh" ubuntu:24.04 bash /c.sh
set -e
apt-get update -qq >/dev/null && apt-get install -y -qq qemu-utils wget >/dev/null 2>&1
cd /work
[ -f resolute-server-cloudimg-amd64.img ] || wget -q https://cloud-images.ubuntu.com/resolute/current/resolute-server-cloudimg-amd64.img
run() { echo "\$ $*"; eval "$@"; echo; }
run qemu-img --version
run ls -lh resolute-server-cloudimg-amd64.img
run qemu-img info resolute-server-cloudimg-amd64.img
run cp resolute-server-cloudimg-amd64.img golden.qcow2
run qemu-img resize golden.qcow2 20G
run time qemu-img create -f qcow2 -b golden.qcow2 -F qcow2 vm1.qcow2
run qemu-img info vm1.qcow2
run ls -lh golden.qcow2 vm1.qcow2
run du -h golden.qcow2 vm1.qcow2
run time qemu-img convert -O raw golden.qcow2 golden.raw
run ls -lh golden.raw
run du -h golden.raw
run qemu-img info golden.raw
run time qemu-img convert -c -O qcow2 golden.qcow2 golden-c.qcow2
run du -h golden.qcow2 golden-c.qcow2
