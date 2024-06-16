import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;

import javax.imageio.ImageIO;
import javax.swing.*;

public class ejercicio1 {
	
	public static class Finestra1 extends JFrame{
		private JPanel panelCheckBoxes, panelButtons, panelMessages;
		private JButton start, exit;
		private JLabel messages;
		private BufferedImage[] arrayImages = new BufferedImage[9];
		private JCheckBox[] arrayCheckBoxes = new JCheckBox[9];

		
		public Finestra1() throws IOException {
			setSize(500,500);
            setDefaultCloseOperation(EXIT_ON_CLOSE);
            setResizable(false);
            setLocationRelativeTo(null);
            
            setTitle("Image selection");
            
            panelCheckBoxes = new JPanel();
            panelCheckBoxes.setLayout(new GridLayout(3,3));
            panelCheckBoxes.setSize(300,300);

            for (int i = 0; i<9 ; i++) {
					BufferedImage imagen = ImageIO.read(new File("./src/Imagen"+i+".jpg"));
					arrayImages[i] = imagen;
					
					Image scaled = imagen.getScaledInstance(80,80, java.awt.Image.SCALE_SMOOTH);
					final JCheckBox checkBox = new JCheckBox("Image "+i, new ImageIcon(scaled), false);
					arrayCheckBoxes[i] = checkBox;

					arrayCheckBoxes[i].addActionListener(new ActionListener() {
		                public void actionPerformed(ActionEvent e) {
		                	String image = e.getActionCommand();
		                	checkBox.getSelectedObjects();
		                	if (checkBox.isSelected()) {
			                	JOptionPane.showMessageDialog(null, image + " is selected" );
		                	} else {
			                	JOptionPane.showMessageDialog(null, image + " is not selected");
		                	}
		                }
		        	});
					panelCheckBoxes.add(checkBox);



            }
            add(panelCheckBoxes, BorderLayout.NORTH);
            
            panelButtons = new JPanel();
            exit = new JButton("Exit");
			exit.addActionListener(new ActionListener() {
                public void actionPerformed(ActionEvent e) {
                	System.exit(0);
                }
        	});
            start = new JButton("Start");
            start.addActionListener(new ActionListener() {
                public void actionPerformed(ActionEvent e) {
                	int count = 0;
                	for (int i = 0;  i < arrayCheckBoxes.length ;i++) {
                		if (arrayCheckBoxes[i].isSelected()) {
                			count += 1;
                		}
                	}
                	if ( count < 5) {
                		messages.setText("At least, 5 images have to be selected.");
                	} else {
                		new Finestra2(arrayCheckBoxes);
                		dispose();
                	}
                }
        	});
            panelButtons.add(exit);
            panelButtons.add(start);
            
            add(panelButtons, BorderLayout.CENTER);
            
            panelMessages = new JPanel();
            messages = new JLabel("Exception Messages");
            panelMessages.add(messages, BorderLayout.CENTER);
            
            add(panelMessages, BorderLayout.SOUTH);
            
        	setVisible(true);
    		
            
            
		}
	}
	
	public static class Finestra2 extends JFrame{
		private JCheckBox[] arrayCheckBoxes = new JCheckBox[9];
		private JPanel panelImg, panelLabels;
		
		public Finestra2(JCheckBox[] arrayCheckBoxes ) {
			this.arrayCheckBoxes = arrayCheckBoxes;
			
		}
	}
	
	public void checkSelectedImages(JCheckBox[] arrayCheckBoxes) {
        ArrayList<BufferedImage> selectedImages = new ArrayList<BufferedImage>();
        for (int i = 0;  i < arrayCheckBoxes.length ;i++) {
    		if (arrayCheckBoxes[i].isSelected()) {
    			selectedImages.add(arrayImages[i]);
    		}
    	}
        if (selectedImages.size() < 5) {
            JOptionPane.showMessageDialog(null, "At least, 5 images have to be selected.");
        } else {
            new Finestra2(arrayCheckBoxes);
        }
		
	}


	public static void main(String[] args) {
		try {
			new Finestra1();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

}
