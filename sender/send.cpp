#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <termios.h>
#include <stdio.h>

#define COLORADO_ADDRESS_WORD_MASK 0x80

#include <string.h>
#include <string>

#define debug

#ifndef WIN32
#include <time.h>
#endif

// Linux headers
#include <errno.h> // Error integer and strerror() function

#include <unistd.h>

//#define  MODEMDEVICE "/dev/ttyUSB0"
//#define MODEMDEVICE "/dev/ttys006"
//#define MODEMDEVICE "/dev/serial0"
#define _POSIX_SOURCE 1 /* POSIX compliant source */
#define FALSE 0
#define TRUE 1

volatile int STOP = FALSE;

int send(char *portname)
{
    char filename[] = "test.txt";
    int fd, c, res;
    struct termios oldtio, newtio;
    FILE *fp;
    char buff[255];

    struct timespec ts;
    ts.tv_sec = 0;
    // ts.tv_nsec = 100000000;
    ts.tv_nsec = 20000;

    printf("using %s \n", portname);

    fd = open(portname, O_RDWR | O_NOCTTY);
    if (fd < 0)
    {
        perror(portname);
        return 1;
    }

    tcgetattr(fd, &oldtio); /* save current port settings */

    bzero(&newtio, sizeof(newtio));
    newtio.c_cflag = ~CRTSCTS & ~PARENB & ~CSTOPB;
    newtio.c_cflag |= CS8 | CLOCAL | CREAD;
    cfsetispeed(&newtio, B4800);
    cfsetospeed(&newtio, B4800);

    //newtio.c_cflag = BAUDRATE | ~CRTSCTS | CS8 | CLOCAL | CREAD;
    newtio.c_iflag = IGNPAR;
    newtio.c_oflag = 0;

    /* set input mode (non-canonical, no echo,...) */
    newtio.c_lflag = 0;

    newtio.c_cc[VTIME] = 0; /* inter-character timer unused */
    newtio.c_cc[VMIN] = 1;  /* blocking read until 5 chars received */

    tcflush(fd, TCIFLUSH);
    tcsetattr(fd, TCSANOW, &newtio);

    printf("ready\n");
    fflush(stdout);

    printf("opening file %s\n", filename);

    if (!(fp = fopen(filename, "r")))
    {
        printf("error opening file\n");
        return 1;
    }

    int i = 0;
    bool isfirst = true;

    char hexa[2];

    while (fgets(buff, 255, (FILE *)fp) != NULL)
    {
        i++;

#ifdef debug
        printf("line %d\n", i);
#endif

        for (int g = 0; g < strlen(buff); g++)
        {
            if (isfirst)
            {
                isfirst = false;
                hexa[0] = buff[g];
            }
            else
            {
                isfirst = true;
                hexa[1] = buff[g];
                int num = (int)strtol(hexa, NULL, 16); // number base 16


#ifdef debug
                printf("%02x ", num);

                if (num == 0x00)
                {
                    printf(".");
                }
#endif
                unsigned char mychar = num;

#ifdef debug
                if (mychar & COLORADO_ADDRESS_WORD_MASK) == COLORADO_ADDRESS_WORD_MASK)
                {
                    printf("\n %02x \n", COLORADO_ADDRESS_WORD_MASK);
                }
#endif

                res = write(fd, &mychar, sizeof mychar);
            }
        }
// wait some time
#ifdef WIN32
        Sleep(100);
#else
        nanosleep(&ts, NULL);
#endif
    }

    fclose(fp);

    //unsigned char text = "hello";
    printf("\n\n");
    //char message[] = "\xbe\x70\x6f\x5f\x40\x30\x20\xa1\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\xbc\x0e\x1e\x20\x30\x4d\x5d\x6a\x7e\xbd\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\xba\x0d\x1a\x20\x30\x4c\x59\x66\x77\xbb\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\xb8\x0c\x19\x20\x30\x4b\x5f\x6e\x79\xb9\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\xb6\x0b\x18\x20\x30\x4b\x5c\x6d\x77\xb7\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\xbe\x70\x6f\x5f\x40\x30\x20\xb4\x0a\x17\x20\x30\x4a\x5d\x6f\x78\xb5\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\xb2\x09\x1d\x20\x30\x4d\x58\x68\x7b\xb3\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\xb0\x08\x1c\x20\x30\x4c\x5f\x6c\x79\xb1\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\xae\x07\x1b\x20\x30\x4c\x5c\x6b\x7d\xaf\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\x7f";
    //char buf[] = "\x80";

    //res = write(fd, buff, strlen(buf));
    //res = write(fd, message, strlen(message));
    //res = write(fd, buf, strlen(buf));

    printf("write %d\n", res);

    tcsetattr(fd, TCSANOW, &oldtio);
    return 1;
}
