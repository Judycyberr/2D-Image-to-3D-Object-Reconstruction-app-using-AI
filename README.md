# 2D-Image-to-3D-Object-Reconstruction-app-using-AI
### Single 2d image is converted to 3d object using open source AI (TripoSR)

## Follow the following steps to create the app:-

### clone the repositories 
      1.git clone https://github.com/Judycyberr/2D-Image-to-3D-Object-Reconstruction-app-using-AI      
      2.cd flask
      3.git clone https://github.com/VAST-AI-Research/TripoSR.git (run this command inside flask folder)
### create virtual environment on the same directory by using
     1.cd TripoSR
     2.python -m venv venv
     3.venv\Scripts\activate.bat 
     4.pip install torch torchvision torchaudio
     5.pip install --upgrade setuptools
     6.pip install -r requirements.txt
   #### (make sure u do this inside the command prompt)
### create a new flutter apllication 
     1.replace the main.drat file inside the lib folder with our main.dart file
### run the following inside the flutter application
      1.flutter pub get
      2.connect your android device (make sure u enabled usb debigging on the android device)
      3.flutter run
## while ruuning make sure pc and android device is connected to the same network
   **************************************over*********************************************************
