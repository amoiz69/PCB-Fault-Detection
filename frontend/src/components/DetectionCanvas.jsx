// frontend/src/components/DetectionCanvas.jsx
// ---------------------------------------------
// Renders the PCB image with bounding boxes overlaid using an HTML5 Canvas.
//
// Why canvas instead of absolutely-positioned <div>s?
// Canvas lets us draw boxes at sub-pixel precision, scale them correctly
// when the displayed image is smaller than the original, and label them
// without z-index headaches.
//
// Key concept: the image from the backend has a natural size (e.g. 640×480).
// The canvas is displayed at a smaller size on screen. We need to scale
// every bounding box coordinate by (displayWidth / naturalWidth).

import { useEffect, useRef } from "react";

export default function DetectionCanvas({ imageUrl, detections, imageWidth, imageHeight }) {
  const canvasRef = useRef(null);
  const imgRef    = useRef(null);

  // Redraw whenever the image or detections change
  useEffect(() => {
    const canvas = canvasRef.current;
    const img    = imgRef.current;
    if (!canvas || !img || !detections) return;

    const draw = () => {
      const ctx = canvas.getContext("2d");

      // Match canvas internal resolution to displayed size
      canvas.width  = img.clientWidth;
      canvas.height = img.clientHeight;

      // Scale factor: displayed size vs actual pixel size from the model
      const scaleX = img.clientWidth  / imageWidth;
      const scaleY = img.clientHeight / imageHeight;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      detections.forEach(({ bbox, class_name, confidence, color }) => {
        const x = bbox.x1 * scaleX;
        const y = bbox.y1 * scaleY;
        const w = bbox.width  * scaleX;
        const h = bbox.height * scaleY;

        // Box border
        ctx.strokeStyle = color;
        ctx.lineWidth   = 2;
        ctx.strokeRect(x, y, w, h);

        // Label background pill
        const label    = `${class_name} ${(confidence * 100).toFixed(0)}%`;
        ctx.font       = "bold 12px sans-serif";
        const textW    = ctx.measureText(label).width;
        const padX     = 6;
        const padY     = 4;
        const labelH   = 18;

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.roundRect(x - 1, y - labelH - padY * 2, textW + padX * 2, labelH + padY, 4);
        ctx.fill();

        // Label text
        ctx.fillStyle = "#ffffff";
        ctx.fillText(label, x + padX - 1, y - padY - 2);
      });
    };

    // Draw once the image has loaded (may already be loaded from cache)
    if (img.complete) {
      draw();
    } else {
      img.onload = draw;
    }

    // Redraw if the window is resized (display size changes, scale changes)
    window.addEventListener("resize", draw);
    return () => window.removeEventListener("resize", draw);
  }, [imageUrl, detections, imageWidth, imageHeight]);

  return (
    <div style={{ position: "relative", display: "inline-block", width: "100%" }}>
      <img
        ref={imgRef}
        src={imageUrl}
        alt="PCB inspection"
        style={{ width: "100%", display: "block", borderRadius: "8px" }}
      />
      {/* Canvas sits exactly on top of the image */}
      <canvas
        ref={canvasRef}
        style={{
          position: "absolute",
          top: 0, left: 0,
          width: "100%", height: "100%",
          pointerEvents: "none",   // let clicks pass through to the image
        }}
      />
    </div>
  );
}
