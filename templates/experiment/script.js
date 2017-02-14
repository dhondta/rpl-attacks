// since OpenJDK 8, Rhino JS Engine is replaced by Nashorn
// this line provides compatibility so that 'importPackage' can be used
try { load("nashorn:mozilla_compat.js"); } catch(e) {}
importPackage(java.io);

// get plugin instances
visualizer = mote.getSimulation().getCooja().getStartedPlugin("VisualizerScreenshot");
powertracker = mote.getSimulation().getCooja().getStartedPlugin("PowerTracker");

// create log file handlers
log.log("Opening log file writers...\n");
log_serial = new FileWriter("./data/serial.log");                // open serial log file
log_rpl = new FileWriter("./data/rpl.log");                      // open RPL messages log file
log_relationships = new FileWriter("./data/relationships.log");  // open mote relationships log file
log_power = new FileWriter("./data/powertracker.log");           // open power tracker logfile

// re-frame visualizer view
visualizer.resetViewport = 1;
visualizer.repaint();

// set timeout and declare variables
TIMEOUT({{ timeout }}, log.testOK());
var c = 0, i = 1, period = {{ sampling_period }}, screenshot = false, pad = "00000", nbr = "";

// now, start the test
log.log("Starting stript...\n");
visualizer.takeScreenshot("./data/network_" + pad + ".png", 0, 0);
while(1) {
  try {
    // first, log to serial file
    line = time + "\tID:" + id.toString() + "\t" + msg + "\n"
    if (msg.startsWith("#L ")) {
      log_relationships.write(line);
      log_relationships.flush();
      screenshot = true;
    } else if (msg.startsWith("RPL: ")) {
      log_rpl.write(line);
      log_rpl.flush();
    } else {
      log_serial.write(line);
      log_serial.flush();
    }
    YIELD();
    // then, log power statistics
    if (c < time) {
      log_power.write(powertracker.radioStatistics());
      log_power.flush();
      if (screenshot) {
        nbr = "" + i;
        nbr = pad.substring(0, pad.length - nbr.length) + nbr;
        visualizer.takeScreenshot("./data/network_" + nbr + ".png", 0, 0);
        i += 1;
      }
      c += period;
    }
  } catch (e) {
    log_serial.close();
    log_rpl.close();
    log_relationships.close();
    log_power.close();
    log.log("File writers closed\n");
    if (c == 0) { log.testFailed(); } else { break; }
    break;
  }
}
log.log("Done.");
