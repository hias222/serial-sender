# test serial

## create intzernal com

fast  
socat -d -d pty,raw,echo=0 pty,raw,echo=0

create port in linux and send from shell to it

```bash
# sending part from shell
socat -d -d - pty,raw,echo=0

# receving from /dev/... - output above
cat < /dev/ttys002
```

create to ports

```bash
socat -d -d pty,raw,echo=0 pty,raw,echo=0
#
# 2023/04/11 19:27:15 socat[81518] N PTY is /dev/ttys002
# 2023/04/11 19:27:15 socat[81518] N PTY is /dev/ttys004
# 2023/04/11 19:27:15 socat[81518] N starting data transfer loop with FDs [5,5] and [7,7]
```


## create data

echo -ne '\xbe\x70\x6f\x5f\x40\x30\x20\xa1\x0d\x1f\x2f\x3f' > /dev/ttys001