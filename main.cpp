#include <iostream>

#ifdef _WIN32
#include <sendwin.h>
#else
#include "send.h"
#endif

int main(int, char **)
{
    printf("start....\n");
    //printf("for internal testing socat -d -d pty,raw,echo=0 pty,raw,echo=0 ");
    send();
}
