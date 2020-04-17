#include <stdio.h>


#ifdef _WIN32
#include <process.h>
#include <Windows.h>
#include <iostream>
#else
#include <unistd.h>
#endif

#include "send.h"

int main()
{
    printf("hello");
    send();
    return 0;
}