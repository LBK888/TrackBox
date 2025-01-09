# TrackBox: An Open-Source Larvae Tracking and Monitoring System
For imaging zebrafish 6~7 dpf old zebrafish larvae

This project builds upon our preliminary research to further design and develop a versatile and cost-effective larvae tracking photography box compatible with 6-well and 24-well plates. 
The software includes a Python application for imaging and an Arduino IDE script for temperature and humidity recording. 
The initial versions of the software are openly available on here, while the hardware design is being updated to version 2.0:
![image](https://github.com/user-attachments/assets/09ddda8b-0829-4957-b8d4-dd187f2da1c2)

## Key Features
- **Cost-Effective and Compatible**  
  Compatible with 6-well and 24-well plates, with material costs under 5000 TWD. For experiments using 6–7 days post-fertilization (dpf) zebrafish, each well can hold 5–7 fish, adjustable to 1–10 fish per well as needed.
- **Foldable and Portable Design**  
  The hardware features a foldable structure (Figure 14, bottom left), facilitating easy shipment to collaborating laboratories that cannot fabricate it themselves.  
- **Open Source**  
  Both hardware and software are open source and available on GitHub, with ongoing updates aligned with project milestones.  

## Technical Specifications
- **Camera**: SONY IMX179 sensor supporting 2592×1944 resolution at 20 fps. USB UVC-compatible, requiring no drivers for direct usage.  
- **Environment Monitoring**: Equipped with an AHT10 sensor to record temperature and humidity during imaging, ensuring experiments are conducted under stable environmental conditions.  
- **Lighting**: The base features an LED white light panel for uniform illumination.  
- **Multi-Box Support**: The imaging software supports simultaneous operation with 2–4 photography boxes, enhancing experimental efficiency.  

This system significantly reduces experimental costs and improves efficiency for zebrafish locomotion behavior studies. Contributions, feedback, and collaborations are welcomed!

## DIY Parts
- **3D printing**: See 3D parts folder
- **Laser cutting**: See Laser parts folder

## Electrical Parts
- **Camera**: USB 800 Megapixels ([DFROBOT FIT0729](https://www.dfrobot.com/product-2188.html))
- **Light box**: 15cm *2 - 5V COB 6000k (white light) LED stripe (5mm wide, 400 LED/meter), or 5050 LEDs 
- **Sensor**: (optional) temperature and humidity sensor, [AHT10](https://a.co/d/ckcVx5F)
- **MCU**: (optional) for temp+humid [D1 mini](https://a.co/d/eWSJpXV)

## Installation
Please read this pdf manual for assembling upper part
