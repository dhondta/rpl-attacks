/*
 * Copyright (c) 2012, Swedish Institute of Computer Science.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the Institute nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE INSTITUTE AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE INSTITUTE OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 * This file is part of the Contiki operating system.
 *
 */

#include "contiki.h"
#include "contiki-lib.h"
#include "contiki-net.h"

#include <string.h>

#define DEBUG DEBUG_FULL
#include "net/ip/uip-debug.h"
#include "dev/watchdog.h"
#include "dev/leds.h"
#include "net/rpl/rpl.h"
#include "dev/button-sensor.h"
#include "debug.h"

#define UIP_IP_BUF   ((struct uip_ip_hdr *)&uip_buf[UIP_LLH_LEN])
#define UIP_UDP_BUF  ((struct uip_udp_hdr *)&uip_buf[uip_l2_l3_hdr_len])
#define UDP_IP_BUF   ((struct uip_udpip_hdr *)&uip_buf[UIP_LLH_LEN])
#define MAX_PAYLOAD_LEN 120

{{ constants }}

static struct uip_udp_conn *server_conn;
static char buf[MAX_PAYLOAD_LEN];
static uint16_t len;
/*---------------------------------------------------------------------------*/
PROCESS(sensor_process, "Malicious sensor process");
AUTOSTART_PROCESSES(&sensor_process);
/*---------------------------------------------------------------------------*/
#if (BUTTON_SENSOR_ON && (DEBUG==DEBUG_PRINT))
static void print_stats() {
  PRINTF("tl=%lu, ts=%lu, bs=%lu, bc=%lu\n",
         RIMESTATS_GET(toolong), RIMESTATS_GET(tooshort),
         RIMESTATS_GET(badsynch), RIMESTATS_GET(badcrc));
  PRINTF("llrx=%lu, lltx=%lu, rx=%lu, tx=%lu\n", RIMESTATS_GET(llrx),
         RIMESTATS_GET(lltx), RIMESTATS_GET(rx), RIMESTATS_GET(tx));
}
#endif
/*---------------------------------------------------------------------------*/
static void print_local_addresses(void) {
  int i;
  uint8_t state;

  PRINTF("Malicious sensor IPv6 addresses:\n");
  for(i = 0; i < UIP_DS6_ADDR_NB; i++) {
    state = uip_ds6_if.addr_list[i].state;
    if(uip_ds6_if.addr_list[i].isused && (state == ADDR_TENTATIVE || state
        == ADDR_PREFERRED)) {
      PRINTF("  ");
      PRINT6ADDR(&uip_ds6_if.addr_list[i].ipaddr);
      PRINTF("\n");
      if(state == ADDR_TENTATIVE) {
        uip_ds6_if.addr_list[i].state = ADDR_PREFERRED;
      }
    }
  }
}
/*---------------------------------------------------------------------------*/
 static void
 tcpip_handler(void)
 {
   static int seq_id;
   char buf[MAX_PAYLOAD_LEN];
   if(uip_newdata()) {
	/*do something...*/
   }
 }

/*---------------------------------------------------------------------------*/
  PROCESS_THREAD(sensor_process, ev, data) {
  PROCESS_BEGIN();
  PRINTF("Starting UDP server (malicious)\n");

#if BUTTON_SENSOR_ON
  PRINTF("Button 1: Print RIME stats\n");
#endif
  print_local_addresses();
  server_conn = udp_new(NULL, UIP_HTONS(0), NULL);
  udp_bind(server_conn, UIP_HTONS(3000));
  PRINTF("Malicious sensor listening on UDP port %u\n", UIP_HTONS(server_conn->lport));

   while(1) {
     PROCESS_YIELD();
     if(ev == tcpip_event) {
       tcpip_handler();
     }
   }
   PROCESS_END();
}
/*---------------------------------------------------------------------------*/
