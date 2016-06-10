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
#include "net/ip/uip-debug.h"
#include "dev/watchdog.h"
#include "dev/leds.h"
#include "net/rpl/rpl.h"
#include "dev/button-sensor.h"
#include "debug.h"
#include <string.h>
#define DEBUG 1
#if DEBUG
#include <stdio.h>
#define PRINTF(...) printf(__VA_ARGS__)
#define PRINT6ADDR(addr) PRINTF(" %02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x ", ((u8_t *)addr)[0], ((u8_t *)addr)[1], ((u8_t *)addr)[2], ((u8_t *)addr)[3], ((u8_t *)addr)[4], ((u8_t *)addr)[5], ((u8_t *)addr)[6], ((u8_t *)addr)[7], ((u8_t *)addr)[8], ((u8_t *)addr)[9], ((u8_t *)addr)[10], ((u8_t *)addr)[11], ((u8_t *)addr)[12], ((u8_t *)addr)[13], ((u8_t *)addr)[14], ((u8_t *)addr)[15])
#define PRINTLLADDR(lladdr) PRINTF(" %02x:%02x:%02x:%02x:%02x:%02x ",(lladdr)->addr[0], (lladdr)->addr[1], (lladdr)->addr[2], (lladdr)->addr[3],(lladdr)->addr[4], (lladdr)->addr[5])
#else
#define PRINTF(...)
#define PRINT6ADDR(addr)
#define PRINTLLADDR(addr)
#endif

#define UDP_IP_BUF   ((struct uip_udpip_hdr *)&uip_buf[UIP_LLH_LEN])

#define MAX_PAYLOAD_LEN 120

static struct uip_udp_conn *server_conn;
static uip_ipaddr_t ipaddr;

PROCESS(udp_server_process, "UDP server process");
AUTOSTART_PROCESSES(&udp_server_process);
/*---------------------------------------------------------------------------*/
static void
tcpip_handler(void)
{
  static int seq_id;
  char buf[MAX_PAYLOAD_LEN];
  if(uip_newdata()) {
     ((char *)uip_appdata)[uip_datalen()] = 0;
     PRINTF("Server received: '%s' from ", (char *)uip_appdata);
     PRINT6ADDR(&UDP_IP_BUF->srcipaddr);
     PRINTF("\n");

     uip_ipaddr_copy(&server_conn->ripaddr, &UDP_IP_BUF->srcipaddr);
     server_conn->rport = UDP_IP_BUF->srcport;
     PRINTF("Responding with message: ");
     sprintf(buf, "Reply - (%d)", ++seq_id);
     PRINTF("%s\n", buf);

     uip_udp_packet_send(server_conn, buf, strlen(buf));
     /* Restore server connection to allow data from any node */
     memset(&server_conn->ripaddr, 0, sizeof(server_conn->ripaddr));
     server_conn->rport = 0;
  }
}
/*---------------------------------------------------------------------------*/
static void
print_local_addresses(void)
{
  int i;
  uint8_t state;

  PRINTF("Server IPv6 addresses: ");
  for(i = 0; i < UIP_CONF_NETIF_MAX_ADDRESSES; i++) {
     state = uip_ds6_if.addr_list[i].state;
     if(state == ADDR_TENTATIVE || state == ADDR_PREFERRED) {
        PRINT6ADDR(&uip_ds6_if.addr_list[i].ipaddr);
        PRINTF("\n");
     }
  }
}
/*---------------------------------------------------------------------------*/
void create_dag() {
  rpl_dag_t *dag;

  uip_ip6addr(&ipaddr, 0xaaaa, 0, 0, 0, 0, 0, 0, 0);
  uip_ds6_set_addr_iid(&ipaddr, &uip_lladdr);
  uip_ds6_addr_add(&ipaddr, 0, ADDR_AUTOCONF);

  print_local_addresses();

  dag = rpl_set_root(RPL_DEFAULT_INSTANCE,
                     &uip_ds6_get_global(ADDR_PREFERRED)->ipaddr);
  if(dag != NULL) {
     uip_ip6addr(&ipaddr, 0xaaaa, 0, 0, 0, 0, 0, 0, 0);
     rpl_set_prefix(dag, &ipaddr, 64);
     PRINTF("Created a new RPL dag with ID: ");
     PRINT6ADDR(&dag->dag_id);
     PRINTF("\n");
  }
}

/*---------------------------------------------------------------------------*/
PROCESS_THREAD(udp_server_process, ev, data)
{
  static struct etimer timer;

  PROCESS_BEGIN();
  PRINTF("UDP server started\n");
  create_dag();
  // wait 5 second, in order to have the IP addresses well configured
  etimer_set(&timer, CLOCK_CONF_SECOND*5);

  // wait until the timer has expired
  PROCESS_WAIT_EVENT_UNTIL(ev == PROCESS_EVENT_TIMER);

  print_local_addresses();

  // set NULL and 0 as IP address and port to accept packet from any node and any srcport.
  server_conn = udp_new(NULL, UIP_HTONS(0), NULL);
  if(server_conn == NULL) {
     PRINTF("No UDP connection available, exiting the process!\n");
     PROCESS_EXIT();
  }
  //bind the connection to server's local port
  udp_bind(server_conn, UIP_HTONS(3000));
  PRINTF("Server listening on UDP port %u\n", UIP_HTONS(server_conn->lport));
  PRINTF("Created a server connection with remote address ");
  PRINT6ADDR(&server_conn->ripaddr);

  while(1) {
    PROCESS_YIELD();
      if(ev == tcpip_event) {
        tcpip_handler();
      }else if (ev == sensors_event && data == &button_sensor) {
        PRINTF("Initiating global repair\n");
        rpl_repair_root(RPL_DEFAULT_INSTANCE);
      }
    }
  PROCESS_END();
}
/*-----*/
