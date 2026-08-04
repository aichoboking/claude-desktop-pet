@echo off
rem 두 마리(백이+깜이)를 각각 따로 움직이는 독립 창으로 띄웁니다.
rem slot 0 = 주인(백이): 두 마리 사이에 "백이 & 깜이" 말풍선 하나를 담당.
rem slot 1 = 짝꿍(깜이): 조용히 움직임만. 각자 드래그로 위치 이동 가능.
start "" pythonw "%~dp0pet.pyw" baek 0 kkam
start "" pythonw "%~dp0pet.pyw" kkam 1
