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
 */

import java.awt.Graphics;
import java.awt.Point;
import java.awt.event.InputEvent;
import java.awt.event.MouseEvent;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.Collection;
import javax.imageio.ImageIO;
import javax.swing.JPanel;

import org.apache.log4j.Logger;

import org.contikios.cooja.Cooja;
import org.contikios.cooja.Simulation;
import org.contikios.cooja.PluginType;
import org.contikios.cooja.ClassDescription;
import org.contikios.cooja.plugins.Visualizer;
import org.contikios.cooja.plugins.VisualizerSkin;
import org.contikios.cooja.plugins.skins.GridVisualizerSkin;
import org.contikios.cooja.plugins.skins.IDVisualizerSkin;
import org.contikios.cooja.plugins.skins.MoteTypeVisualizerSkin;
import org.contikios.cooja.plugins.skins.UDGMVisualizerSkin;

import org.jdom.Element;

/**
 * Extension of Visualizer to give the possibility to screenshot visualizer's
 *  content
 *
 * @author Alexandre D'Hondt
 * @author Hussein Bahmad
 */

@ClassDescription("Visualizer screenshot")
@PluginType(PluginType.SIM_PLUGIN)
public class VisualizerScreenshot extends Visualizer {

  private static final Logger logger = Logger.getLogger(VisualizerScreenshot.class);

  private JPanel canvas;
  private Visualizer visualizer;
  private VisualizerSkin[] currentSkins;
  private Point point;

  public VisualizerScreenshot(Simulation simulation, Cooja cooja) {
    super(simulation, cooja);
    logger.info("Starting visualizer screenshot");
  }

  public String takeScreenshot(String path) {
    return takeScreenshot(path, 0, 0, 0);
  }

  public String takeScreenshot(String path, double x, double y) {
    return takeScreenshot(path, (int) x, (int) y, 0);
  }

  public String takeScreenshot(String path, int x, int y) {
    return takeScreenshot(path, x, y, 0);
  }

  public String takeScreenshot(String path, double x, double y, double z) {
    return takeScreenshot(path, (int) x, (int) y, (int) z);
  }

  public String takeScreenshot(String path, int x, int y, int z) {
    if (!Cooja.isVisualized()) {
      return "Visualizer Screenshot only works in GUI mode";
    }
    // first, retrieve the panel instance and the selected skins
    canvas = getCurrentCanvas();
    currentSkins = getCurrentSkins();
    // create and initialize the image
    BufferedImage image = new BufferedImage(canvas.getSize().width, canvas.getSize().height, BufferedImage.TYPE_INT_ARGB);
    Graphics g = image.createGraphics();
    // select an element (as if it was clicked)
    point = transformPositionToPixel(x, y, z);
    canvas.dispatchEvent(new MouseEvent(canvas, MouseEvent.MOUSE_PRESSED, 1,
                                        InputEvent.BUTTON1_MASK, (int) point.getX(), (int) point.getY(), 1, false));
    // draw the panel in the image
    for (VisualizerSkin skin : currentSkins) {
      if (skin instanceof GridVisualizerSkin ||
          skin instanceof IDVisualizerSkin ||
          skin instanceof MoteTypeVisualizerSkin ||
          skin instanceof UDGMVisualizerSkin) {
        skin.paintBeforeMotes(g);
      }
    }
    paintMotes(g);
    for (VisualizerSkin skin : currentSkins) {
      if (skin instanceof GridVisualizerSkin ||
          skin instanceof IDVisualizerSkin ||
          skin instanceof MoteTypeVisualizerSkin ||
          skin instanceof UDGMVisualizerSkin) {
        skin.paintAfterMotes(g);
      }
    }
     // finally, try to save the image
    String ext = path.substring(path.lastIndexOf(".") + 1);
    try {
      File output = new File(path);
      ImageIO.write(image, ext, output);
      return "Screenshot saved at '" + path + "'\n";
    } catch (Exception e) {
      StringWriter sw = new StringWriter();
      PrintWriter pw = new PrintWriter(sw);
      e.printStackTrace(pw);
      return sw.toString();
    }
  }

}
