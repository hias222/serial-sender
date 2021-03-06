#include <stdio.h>
#include <string.h>
#include <string>

// Linux headers
#include <fcntl.h> // Contains file controls like O_RDWR
#include <errno.h> // Error integer and strerror() function

// https://gitlab.com/Teuniz/RS-232/-/tree/master

#ifdef _WIN32
#include <Windows.h>
#include <assert.h>
#include <tchar.h>
#endif

#define RS232_PORTNR 32
#define COLORADO_ADDRESS_WORD_MASK 0x80

DWORD NoBytesWrite;
using namespace std;

void PrintCommState(DCB dcb)
{
    //  Print some of the DCB structure values
    _tprintf(TEXT("\nBaudRate = %d, ByteSize = %d, Parity = %d, StopBits = %d\n"),
             dcb.BaudRate,
             dcb.ByteSize,
             dcb.Parity,
             dcb.StopBits);
}

int send(char *portname)
{
    int comport_number = atoi(portname);
    //HANDLE Cport[RS232_PORTNR];
    const char *comports[RS232_PORTNR] = {"\\\\.\\COM1", "\\\\.\\COM2", "\\\\.\\COM3", "\\\\.\\COM4",
                                          "\\\\.\\COM5", "\\\\.\\COM6", "\\\\.\\COM7", "\\\\.\\COM8",
                                          "\\\\.\\COM9", "\\\\.\\COM10", "\\\\.\\COM11", "\\\\.\\COM12",
                                          "\\\\.\\COM13", "\\\\.\\COM14", "\\\\.\\COM15", "\\\\.\\COM16",
                                          "\\\\.\\COM17", "\\\\.\\COM18", "\\\\.\\COM19", "\\\\.\\COM20",
                                          "\\\\.\\COM21", "\\\\.\\COM22", "\\\\.\\COM23", "\\\\.\\COM24",
                                          "\\\\.\\COM25", "\\\\.\\COM26", "\\\\.\\COM27", "\\\\.\\COM28",
                                          "\\\\.\\COM29", "\\\\.\\COM30", "\\\\.\\COM31", "\\\\.\\COM32"};

    //char mode_str[128];

    HANDLE hComm; // Handle to the Serial port
    BOOL Status;  // Status
    OVERLAPPED o;
    DCB dcbSerialParams = {0};   // Initializing DCB structure
    COMMTIMEOUTS timeouts = {0}; //Initializing timeouts structure
    DWORD BytesWritten = 0;      // No of bytes written to the port
    DWORD dwEventMask;           // Event mask to trigger
    //char ReadData;               //temperory Character
    uint8_t ReadData;
    DWORD NoBytesRead; // Bytes read by ReadFile()
    unsigned char loop = 0;
    wchar_t pszPortName[10] = {0}; //com port id
    wchar_t PortNo[20] = {0};      //contain friendly name

    FILE *fp;
    char filename[] = "test.txt";
    char buff[255];

    printf("port: %s \n", comports[comport_number]);
    fflush(stdout);
    try
    {
        hComm = CreateFileA(comports[comport_number],
                            GENERIC_READ | GENERIC_WRITE,
                            0,    /* no share  */
                            NULL, /* no security */
                            OPEN_EXISTING,
                            0,     /* no threads */
                            NULL); /* no templates */

        if (hComm == INVALID_HANDLE_VALUE)
        {
            printf_s("\n Port can't be opened\n\n");
            return 1;
        }

        SecureZeroMemory(&dcbSerialParams, sizeof(DCB));
        dcbSerialParams.DCBlength = sizeof(DCB);

        Status = GetCommState(hComm, &dcbSerialParams); //retreives  the current settings
        if (Status == FALSE)
        {
            printf_s("\nError to Get the Com state\n\n");
            return 1;
        }

        dcbSerialParams.BaudRate = CBR_9600;   //BaudRate = 9600
        dcbSerialParams.ByteSize = 8;          //ByteSize = 8
        dcbSerialParams.StopBits = ONESTOPBIT; //StopBits = 1
        dcbSerialParams.Parity = EVENPARITY; // NOPARITY Parity = None

        Status = SetCommState(hComm, &dcbSerialParams);

        if (Status == FALSE)
        {
            printf_s("\nError to Setting DCB Structure\n\n");
            return false;
        }

        printf("set colorado Parameters (9600, ByteSize = 8, Parity = 2, StopBits = 0)");
        Status = GetCommState(hComm, &dcbSerialParams); //retreives  the current settings

        if (Status == FALSE)
        {
            printf_s("\nError to Get the Com state\n\n");
            return 1;
        }

        PrintCommState(dcbSerialParams);

        //Setting Timeouts
        timeouts.ReadIntervalTimeout = 50;
        timeouts.ReadTotalTimeoutConstant = 50;
        timeouts.ReadTotalTimeoutMultiplier = 10;
        timeouts.WriteTotalTimeoutConstant = 50;
        timeouts.WriteTotalTimeoutMultiplier = 10;

        if (SetCommTimeouts(hComm, &timeouts) == FALSE)
        {
            printf_s("\nError to Setting Time outs");
            return false;
        }

        //Setting Receive Mask
        Status = SetCommMask(hComm, EV_RXCHAR);
        if (Status == FALSE)
        {
            printf_s("\nError to in Setting CommMask\n\n");
            return false;
        }

        /*
        //Setting WaitComm() Event
        Status = WaitCommEvent(hComm, &dwEventMask, NULL); //Wait for the character to be received

        if (Status == FALSE)
        {
            printf_s("\nError! in Setting WaitCommEvent()\n\n");
            return false;
        }
        */

        //Read data and store in a buffer

        // Create an event object for use by WaitCommEvent.

        o.hEvent = CreateEvent(
            NULL,  // default security attributes
            TRUE,  // manual-reset event
            FALSE, // not signaled
            NULL   // no name
        );

        // Initialize the rest of the OVERLAPPED structure to zero.
        o.Internal = 0;
        o.InternalHigh = 0;
        o.Offset = 0;
        o.OffsetHigh = 0;

        assert(o.hEvent);

        bool connectsuccess = true;
        int i = 0;

        printf("opening file %s\n", filename);

        if (!(fp = fopen(filename, "r")))
        {
            printf("error opening file\n");
            return 1;
        }

        int ik = 0;
        bool isfirst = true;
        char *hexa = new char[2];

        while (fgets(buff, 255, (FILE *)fp) != NULL)
        {
            ik++;
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
                    WriteFile(hComm, &mychar, sizeof(mychar), &NoBytesWrite, NULL);

                    printf("%02x ", mychar);
                    if ((mychar & COLORADO_ADDRESS_WORD_MASK) == COLORADO_ADDRESS_WORD_MASK)
                    {
                        printf("\n");
                    }
                }
            }
#ifdef WIN32
            Sleep(100);
#else
            nanosleep(&ts, NULL);
#endif
        }

        /*
        char message[] = "\xbe\x70\x6f\x5f\x40\x30\x20\xa1\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\xbc\x0e\x1e\x20\x30\x4d\x5d\x6a\x7e\xbd\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\xba\x0d\x1a\x20\x30\x4c\x59\x66\x77\xbb\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\xb8\x0c\x19\x20\x30\x4b\x5f\x6e\x79\xb9\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\xb6\x0b\x18\x20\x30\x4b\x5c\x6d\x77\xb7\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\xbe\x70\x6f\x5f\x40\x30\x20\xb4\x0a\x17\x20\x30\x4a\x5d\x6f\x78\xb5\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\xb2\x09\x1d\x20\x30\x4d\x58\x68\x7b\xb3\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\xb0\x08\x1c\x20\x30\x4c\x5f\x6c\x79\xb1\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\xae\x07\x1b\x20\x30\x4c\x5c\x6b\x7d\xaf\x0d\x1f\x2f\x3f\x4d\x5d\x6f\x7f\x7f";
        char buf[] = "\x80";

        Status = WriteFile(hComm, buf, strlen(buf), &NoBytesWrite, NULL);
        Status = WriteFile(hComm, message, strlen(message), &NoBytesWrite, NULL);
        Status = WriteFile(hComm, buf, strlen(buf), &NoBytesWrite, NULL);
*/
        CloseHandle(hComm); //Closing the Serial Port
        printf("closing \n");
    }
    catch (...)
    {
        printf("Exception occurred");
        return false;
    }
    printf("end \n");
    return 0;
}
