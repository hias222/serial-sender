#include <string>

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <ctype.h>

#include "pigpio.h"

#define CE0 5
#define CE1 6
#define MISO 13
#define MOSI 19
#define SCLK 12

#define debug

#define COLORADO_ADDRESS_WORD_MASK 0x80

//#define MODEMDEVICE "/dev/serial0"

using namespace std;

int send(char *portname)
{

    int USBHandle, e;
    uint b;
    int order;
    FILE *fp;
    char *TEXT;
    char text[2048];
    char buff[255];

    char filename[] = "test.txt";

    if (gpioInitialise() < 0)
    {
        fprintf(stderr, "pigpio initialisation failed.\n");
        return 1;
    }

    USBHandle = serOpen(portname, 9600, 0);

    if (USBHandle < 0)
    {
        fprintf(stderr, "USBHandle failed.\n");
        return 1;
    }

    printf("   Serial port (GPIO) = %s\n", portname);

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

#ifdef debug
                printf("start reading file\n",);
#endif

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
                //int serWrite(unsigned handle, char *buf, unsigned count)
                serWrite(USBHandle, &mychar, sizeof mychar);
#ifdef debug
                printf("%02x ", num);
#endif

                //res = write(fd, &mychar, sizeof mychar);
            }
        }
    }

    fclose(fp);
    printf("\n\n");
    serClose(USBHandle);
    gpioTerminate();

    return 0;
}
