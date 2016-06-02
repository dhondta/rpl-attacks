<?xml version="1.0" encoding="UTF-8"?>
<simconf>
  <project EXPORT="discard">[CONTIKI_DIR]/tools/cooja/apps/mrm</project>
  <project EXPORT="discard">[CONTIKI_DIR]/tools/cooja/apps/mspsim</project>
  <project EXPORT="discard">[CONTIKI_DIR]/tools/cooja/apps/avrora</project>
  <project EXPORT="discard">[CONTIKI_DIR]/tools/cooja/apps/powertracker</project>
  <project EXPORT="discard">[CONTIKI_DIR]/tools/cooja/apps/serial_socket</project>
  <project EXPORT="discard">[CONTIKI_DIR]/tools/cooja/apps/visualizer_screenshot</project>
  <simulation>
    <title>{{ title }}</title>
    <randomseed>generated</randomseed>
    <motedelay_us>1000000</motedelay_us>
    <radiomedium>
      org.contikios.cooja.radiomediums.UDGM
      <transmitting_range>{{ transmitting_range }}</transmitting_range>
      <interference_range>{{ interference_range }}</interference_range>
      <success_ratio_tx>{{ success_ratio_tx }}</success_ratio_tx>
      <success_ratio_rx>{{ success_ratio_rx }}</success_ratio_rx>
    </radiomedium>
    <events>
      <logoutput>40000</logoutput>
    </events>
    {% for mote_type in mote_types %}<motetype>
      org.contikios.cooja.mspmote.{{ target_capitalized }}MoteType
      <identifier>{{ mote_type.name }}</identifier>
      <description>{{ mote_type.description }}</description>
      <firmware EXPORT="copy">[CONFIG_DIR]/motes/{{ mote_type.name }}.{{ mote_type.target }}</firmware>
      <moteinterface>org.contikios.cooja.interfaces.Position</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.RimeAddress</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.IPAddress</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.Mote2MoteRelations</moteinterface>
      <moteinterface>org.contikios.cooja.interfaces.MoteAttributes</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspClock</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspMoteID</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspButton</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.Msp802154Radio</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspDefaultSerial</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspLED</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspSerial</moteinterface>
      <moteinterface>org.contikios.cooja.mspmote.interfaces.MspDebugOutput</moteinterface>
    </motetype>
    {% endfor %}{% for mote in motes %}
    <mote>
      <breakpoints />
      <interface_config>
        org.contikios.cooja.interfaces.Position
        <x>{{ mote.x }}</x>
        <y>{{ mote.y }}</y>
        <z>{{ mote.z }}</z>
      </interface_config>
      <interface_config>
        org.contikios.cooja.mspmote.interfaces.MspClock
        <deviation>1.0</deviation>
      </interface_config>
      <interface_config>
        org.contikios.cooja.mspmote.interfaces.MspMoteID
        <id>{{ mote.id }}</id>
      </interface_config>
      <motetype_identifier>{{ mote.type }}</motetype_identifier>
    </mote>
    {% endfor %}
  </simulation>
  <plugin>
    org.contikios.cooja.plugins.ScriptRunner
    <plugin_config>
      <scriptfile>[CONFIG_DIR]/script.js</scriptfile>
      <active>true</active>
      <split>250</split>
    </plugin_config>
    <width>790</width>
    <height>450</height>
    <location_x>1050</location_x>
    <location_y>0</location_y>
    <z>2</z>
  </plugin>
  <plugin>
    org.contikios.cooja.plugins.SimControl
    <width>280</width>
    <height>120</height>
    <location_x>400</location_x>
    <location_y>450</location_y>
    <z>2</z>
  </plugin>
  <plugin>
    org.contikios.cooja.serialsocket.SerialSocketServer
    <mote_arg>0</mote_arg>
    <width>280</width>
    <height>120</height>
    <location_x>400</location_x>
    <location_y>570</location_y>
    <z>2</z>
  </plugin>
  <plugin>
    PowerTracker
    <plugin_config>
    </plugin_config>
    <width>450</width>
    <height>240</height>
    <location_x>680</location_x>
    <location_y>450</location_y>
    <z>2</z>
  </plugin>
  <plugin>
    VisualizerScreenshot
    <plugin_config>
      <moterelations>true</moterelations>
      <skin>org.contikios.cooja.plugins.skins.IDVisualizerSkin</skin>
      <skin>org.contikios.cooja.plugins.skins.TrafficVisualizerSkin</skin>
      <skin>org.contikios.cooja.plugins.skins.GridVisualizerSkin</skin>
      <skin>org.contikios.cooja.plugins.skins.MoteTypeVisualizerSkin</skin>
      <skin>org.contikios.cooja.plugins.skins.UDGMVisualizerSkin</skin>
      <viewport>1.5 0.0 0.0 1.5 210.0 170.0</viewport>
    </plugin_config>
    <width>400</width>
    <height>400</height>
    <location_x>1</location_x>
    <location_y>1</location_y>
    <z>1</z>
  </plugin>
  <plugin>
    org.contikios.cooja.plugins.LogListener
    <plugin_config>
      <filter />
      <formatted_time />
      <coloring />
    </plugin_config>
    <width>710</width>
    <height>240</height>
    <location_x>1130</location_x>
    <location_y>450</location_y>
    <z>2</z>
  </plugin>
  <plugin>
    org.contikios.cooja.plugins.RadioLogger
    <plugin_config>
      <split>450</split>
      <formatted_time />
      <showdups>false</showdups>
      <hidenodests>false</hidenodests>
      <analyzers name="6lowpan-pcap" />
      <pcap_file EXPORT="discard">[CONFIG_DIR]/data/output.pcap</pcap_file>
    </plugin_config>
    <width>650</width>
    <height>450</height>
    <location_x>400</location_x>
    <location_y>0</location_y>
    <z>2</z>
  </plugin>
  <plugin>
    org.contikios.cooja.plugins.TimeLine
    <plugin_config>
      {% for mote in motes %}<mote>{{ mote.id }}</mote>
      {% endfor %}<showRadioRXTX />
      <showRadioHW />
      <showLEDs />
      <zoomfactor>500.0</zoomfactor>
    </plugin_config>
    <width>1840</width>
    <height>180</height>
    <location_x>0</location_x>
    <location_y>690</location_y>
    <z>2</z>
    <zoomfactor>500.0</zoomfactor>
  </plugin>
  <plugin>
    org.contikios.cooja.plugins.Notes
    <plugin_config>
      <notes>Goal: {{ goal }}

{{ notes }}</notes>
      <decorations>true</decorations>
    </plugin_config>
    <width>400</width>
    <height>290</height>
    <location_x>1</location_x>
    <location_y>400</location_y>
    <z>1</z>
  </plugin>
</simconf>

