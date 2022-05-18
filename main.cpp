#include <iostream>

#ifdef _WIN32
#include <sendwin.h>
#define BASIC_PORTNAME "2"
#else
#include "send.h"
//#define BASIC_PORTNAME "/dev/ttyAMA0"
//#define BASIC_PORTNAME "/dev/tty.usbserial-146120"
#define BASIC_PORTNAME "/dev/cu.usbserial-FTBTCOC23"
//#define BASIC_PORTNAME "/dev/ttyUSB0"
#endif

void usage(char *prog)
{
    printf("usage %s [-s %s] \n", prog, BASIC_PORTNAME);
    printf("  -s portname      source port name %s \n", BASIC_PORTNAME);
}

int main(int argc, char *argv[])
{
    char *portname = (char *)malloc(50);
    sprintf(portname, "%s", BASIC_PORTNAME);
    bool cmd_line_failure = true;
    for (int n = 1; n < argc; n++) /* Scan through args. */
    {
        switch ((int)argv[n][0]) /* Check for option character. */
        {
        case '-':
            switch ((int)argv[n][1]) /* Check for option character. */
            {
            case 's':
                //printf("we getting source \n");
                if (argc > n)
                {
                    portname = argv[n + 1];
                    cmd_line_failure = false;
                }
                break;
            default:
                usage(argv[0]);
                return 0;
                break;
            }
            break;
        default:
            if (cmd_line_failure)
            {
                usage(argv[0]); /* Not option -- text. */
                return 0;
            }
            break;
        }
    }

    printf("start....\n");

    printf("RPI:\n");
    printf("RPI FTDI not enabled\n");
    printf("RPI lsmod | grep ftdi_sio \n");
    printf("RPI change blacklist /etc/modprobe.d/black.. \n");
    printf("RPI disable service colorado \n");
    printf("RPI reboot \n");
    printf("RPI modprobe ftdi_sio \n");
    printf("RPI ./serial-sender -p /dev/ttyUSB0 \n");

    printf("for mac take /dev/cu.xxx\n");
    printf("for win take 1,2,3...\n");

    //printf("for internal testing socat -d -d pty,raw,echo=0 pty,raw,echo=0 ");
    send(portname);
}
