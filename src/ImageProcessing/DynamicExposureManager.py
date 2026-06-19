import cv2
import numpy as np

class DynamicExposureManager:
    def __init__(self, cap, start_exposure=-5, min_exposure=-12, max_exposure=-1, step=1, threshold_pct=5.0):
        """
        Klasse til dynamisk at styre kameraets lysstyrke.
        
        cap: Dit cv2.VideoCapture(0) objekt
        start_exposure: Den værdi kameraet starter på
        min_exposure: Hvor mørkt kameraet må gå (lavere tal = mørkere billede)
        max_exposure: Hvor lyst kameraet må gå (højere tal = lysere billede)
        step: Hvor hurtigt den justerer per frame (juster op, hvis den reagerer for langsomt)
        threshold_pct: Hvor mange % af billedet der må være helt hvidt (>240), før vi skruer ned
        """
        self.cap = cap
        self.current_exposure = start_exposure
        self.min_exposure = min_exposure
        self.max_exposure = max_exposure
        self.step = step
        self.threshold_pct = threshold_pct
        
        # Initialiser kameraet til manuel eksponering
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) # 1 = Manuel på de fleste webcams
        self.cap.set(cv2.CAP_PROP_EXPOSURE, self.current_exposure)

    def process_frame(self, frame):
        """
        Analyserer det nuværende frame og justerer kameraets hardware, hvis det er for lyst.
        Returnerer det samme frame, så det passer ind i jeres pipeline.
        """
        if frame is None:
            return frame

        # 1. Konverter til gråtone for at måle ren lysstyrke
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 2. Tæl overeksponerede pixels (pixels der er næsten helt hvide)
        overexposed_pixels = np.sum(gray > 240)
        total_pixels = gray.size
        overexposure_ratio = (overexposed_pixels / total_pixels) * 100
        
        # 3. Juster hardwaren hvis tærsklen er overskredet
        if overexposure_ratio > self.threshold_pct:
            if self.current_exposure > self.min_exposure:
                self.current_exposure -= self.step
                self.cap.set(cv2.CAP_PROP_EXPOSURE, self.current_exposure)
                # Valgfrit: print(f"[Lysstyring] Sænker eksponering til {self.current_exposure} ({overexposure_ratio:.1f}% hvidt)")
                
        # 4. Hvis det modsat bliver alt for mørkt generelt (gennemsnit under 40 ud af 255)
        elif np.mean(gray) < 40:
            if self.current_exposure < self.max_exposure:
                self.current_exposure += self.step
                self.cap.set(cv2.CAP_PROP_EXPOSURE, self.current_exposure)
                # Valgfrit: print(f"[Lysstyring] Hæver eksponering til {self.current_exposure}")

        return frame