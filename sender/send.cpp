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
    int fd, c, res, flag, baudrate;
    struct termios oldtio, newtio;
    FILE *fp;
    char buff[255];

    struct timespec ts;
    ts.tv_sec = 0;
    // ts.tv_nsec = 100000000;
    ts.tv_nsec = 10000000;

    printf("using %s \n", portname);

    // fd = open(portname, O_RDWR | O_NOCTTY);
    fd = open(portname, O_RDWR | O_NDELAY);
    if (fd < 0)
    {
        perror(portname);
        return 1;
    }

    printf("open succeded \n");
    tcgetattr(fd, &oldtio); /* save current port settings */

    flag = fcntl(fd, F_GETFL, 0);
    fcntl(fd, F_SETFL, flag & ~O_NDELAY);

    // set baudrate to 0 and go back to normal
    printf("set baudrate to 0......\n");
    tcgetattr(fd, &newtio);
    tcgetattr(fd, &oldtio);
    cfsetospeed(&newtio, B0);
    cfsetispeed(&newtio, B0);
    tcsetattr(fd, TCSANOW, &newtio);
    sleep(1);
    tcsetattr(fd, TCSANOW, &oldtio);
    printf("baudrate is back to normal......\n");

    tcgetattr(fd, &newtio);

    baudrate = B9600;
    // baudrate = B19200;
    cfsetospeed(&newtio, baudrate);
    cfsetispeed(&newtio, baudrate);

    // newtio.c_cflag = (newtio.c_cflag & ~CSIZE) | CS8;

    // set into raw, no echo mode
    newtio.c_iflag = 0;

    newtio.c_lflag = 0;
    newtio.c_oflag = 0;
    newtio.c_cflag = 0;

    newtio.c_cflag = PARENB;

    // 1 stopbit
    newtio.c_cflag &= ~CSTOPB;

    newtio.c_cc[VTIME] = 0; // inter-character timer unused
    newtio.c_cc[VMIN] = 0;  // blocking read until 5 chars received

    tcflush(fd, TCIFLUSH);

    tcsetattr(fd, TCSANOW, &newtio);

    printf("ready in (USB)= %s\n", portname);
    fflush(stdout);

    printf("opening file %s\n", filename);

    int i = 0;
    bool isfirst = true;

    char *hexa = new char[2];

    while (true)
    {
        if (!(fp = fopen(filename, "r")))
        {
            printf("error opening file\n");
            return 1;
        }

        while (fgets(buff, 255, (FILE *)fp) != NULL)
        {
            i++;
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
                    unsigned char mychar = num;

                    // if ((mychar & COLORADO_ADDRESS_WORD_MASK) == COLORADO_ADDRESS_WORD_MASK)
                    //{
                    //     printf("\n");
                    // }
                    // printf("%02x ", mychar);
                    res = write(fd, &mychar, sizeof(mychar));
                }
            }
            // wait some time
            //#ifdef WIN32
            //            Sleep(100);
            //#else
            //            nanosleep(&ts, NULL);
            //#endif
        }
        printf("end test.txt\n");
        fclose(fp);
    }

    printf("\n\n");
    printf("write %d\n", res);

    tcsetattr(fd, TCSANOW, &oldtio);
    return 1;
}
