# 2D-Image-to-3D-Object-Reconstruction-app-using-AI
Single 2d image is converted to 3d object using open source AI (TripoSR)
follow the following steps to create the app :-
1) git clone https://github.com/Judycyberr/2D-Image-to-3D-Object-Reconstruction-app-using-AI
2) cd flask
3) git clone https://github.com/VAST-AI-Research/TripoSR.git
   (run this command inside flask folder
4) create virtual environment on the same directory by using 
     cd TripoSR
     python -m venv venv
     venv\Scripts\activate.bat
     pip install torch torchvision torchaudio
     pip install --upgrade setuptools
     pip install -r requirements.txt
   (make sure u do this inside the command prompt)
5) create a new flutter apllication 
   replace the main.drat file inside the lib folder with our main.dart file
6) run the followinf inside the flutter application
      flutter pub get
   connect your android device (make sure u enabled usb debigging on the android device)
      flutter run

   ***********************************************************************************************
