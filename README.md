# 2D-Image-to-3D-Object-Reconstruction-app-using-AI
Single 2d image is converted to 3d object using open source AI (TripoSR)
!!!!follow the following steps to create the app :-
1) git clone https://github.com/Judycyberr/2D-Image-to-3D-Object-Reconstruction-app-using-AI
      1.cd flask
      2.git clone https://github.com/VAST-AI-Research/TripoSR.git (run this command inside flask folder)
2) create virtual environment on the same directory by using
     1.cd TripoSR
     2.python -m venv venv
     3.venv\Scripts\activate.bat
     4.pip install torch torchvision torchaudio
     5.pip install --upgrade setuptools
     6.pip install -r requirements.txt
   (make sure u do this inside the command prompt)
3) create a new flutter apllication 
     1.replace the main.drat file inside the lib folder with our main.dart file
7) run the following inside the flutter application
      1.flutter pub get
      2.connect your android device (make sure u enabled usb debigging on the android device)
      3.flutter run

   ***********************************************************************************************
