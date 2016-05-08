importPackage(java.io);

serial_log_file = new FileWriter("serial.log");
power_tracker_file = new FileWriter("powertracker.log", false);
power_tracker = mote.getSimulation().getCooja().getStartedPlugin("PowerTracker");

function time_prefix(val){
  var i = 0;
  var array1 = val.split("\n");
  for (i = 0; i &lt; array1.length; i++) { array1[i] = time + array1[i]; }
  val = array1.join("\n");
}

function print_stats() {
  stats = power_tracker.radioStatistics();
  log.log("PowerTracker: Extracted statistics:\n" + stats + "\n");
  time_prefix(stats);
  power_tracker_file.write(stats);
  power_tracker_file.flush();
}

TIMEOUT({{ timeout }}, log.testOK());
counter = 0;
powertracker_frequency = {{ powertracker_frequency }};
if (power_tracker == null) { log.log("No PowerTracker plugin\n"); }

while(1) {
  serial_log_file.write(time + " ID:" + id.toString() + " " + msg + "\n");
  serial_log_file.flush();
  try {
    YIELD();
    if (counter &lt; time){
      log.log(counter);
      if (power_tracker != null) { print_stats(); }
      counter += powertracker_frequency;
    }
  } catch (e) {
    serial_log_file.close();
    power_tracker_file.close();
    throw('test script killed');
    log.testOK();
  }
}
