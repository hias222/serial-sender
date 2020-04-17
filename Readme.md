# test serial

## create intzernal com

socat -d -d pty,raw,echo=0 pty,raw,echo=0

## create data

echo -ne '\xbe\x70\x6f\x5f\x40\x30\x20\xa1\x0d\x1f\x2f\x3f' > /dev/ttys001