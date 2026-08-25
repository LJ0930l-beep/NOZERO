"use client";

import { useEffect, useRef, useState } from "react";

type CameraState = "IDLE" | "PREVIEW_ONLY" | "BLOCKED" | "UNAVAILABLE";

export function CameraPanel() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [state, setState] = useState<CameraState>("IDLE");
  const [message, setMessage] = useState("Camera is optional. Manual mode is always ready.");

  useEffect(() => () => stream?.getTracks().forEach((track) => track.stop()), [stream]);

  async function startCamera() {
    if (!navigator.mediaDevices?.getUserMedia) {
      setState("UNAVAILABLE");
      setMessage("This browser does not expose a camera. Continue in Manual Mode.");
      return;
    }
    try {
      const nextStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
      if (videoRef.current) videoRef.current.srcObject = nextStream;
      setStream(nextStream);
      setState("PREVIEW_ONLY");
      setMessage("Local preview only. Pose analysis is not claimed until calibration and confidence are GOOD.");
    } catch {
      setState("BLOCKED");
      setMessage("Camera permission was not granted. Nothing was uploaded; use Manual Mode instead.");
    }
  }

  function stopCamera() {
    stream?.getTracks().forEach((track) => track.stop());
    setStream(null);
    setState("IDLE");
    setMessage("Camera is optional. Manual mode is always ready.");
  }

  return (
    <div>
      <div className="camera-frame camera-preview">
        {stream ? <video ref={videoRef} autoPlay muted playsInline aria-label="Local camera preview" /> : <div><span>CAMERA CALIBRATION</span><p>{message}</p></div>}
      </div>
      <div className="camera-status"><span className={state === "PREVIEW_ONLY" ? "status-pip" : ""} />{state === "PREVIEW_ONLY" ? "PREVIEW ONLY / NO UPLOAD" : message}</div>
      <button className="button button-secondary camera-action" onClick={stream ? stopCamera : startCamera}>{stream ? "STOP CAMERA" : "ENABLE LOCAL PREVIEW"}</button>
    </div>
  );
}
