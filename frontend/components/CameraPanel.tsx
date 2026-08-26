"use client";

import { useEffect, useRef, useState } from "react";

type CameraState = "IDLE" | "PREVIEW_ONLY" | "BLOCKED" | "UNAVAILABLE";

export function CameraPanel() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [state, setState] = useState<CameraState>("IDLE");
  const [message, setMessage] = useState("摄像头是可选项，手动模式随时可用。");

  useEffect(() => () => stream?.getTracks().forEach((track) => track.stop()), [stream]);

  async function startCamera() {
    if (!navigator.mediaDevices?.getUserMedia) {
      setState("UNAVAILABLE");
      setMessage("当前浏览器没有提供摄像头，请继续使用手动模式。");
      return;
    }
    try {
      const nextStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
      if (videoRef.current) videoRef.current.srcObject = nextStream;
      setStream(nextStream);
      setState("PREVIEW_ONLY");
      setMessage("当前仅为本地预览；完成校准并达到 GOOD 置信度前，不会宣称自动计数。");
    } catch {
      setState("BLOCKED");
      setMessage("未获得摄像头权限，没有任何内容上传；请改用手动模式。");
    }
  }

  function stopCamera() {
    stream?.getTracks().forEach((track) => track.stop());
    setStream(null);
    setState("IDLE");
    setMessage("摄像头是可选项，手动模式随时可用。");
  }

  return (
    <div>
      <div className="camera-frame camera-preview">
        {stream ? <video ref={videoRef} autoPlay muted playsInline aria-label="本地摄像头预览" /> : <div><span>摄像头校准</span><p>{message}</p></div>}
      </div>
      <div className="camera-status"><span className={state === "PREVIEW_ONLY" ? "status-pip" : ""} />{state === "PREVIEW_ONLY" ? "仅本地预览 / 不上传" : message}</div>
      <button className="button button-secondary camera-action" onClick={stream ? stopCamera : startCamera}>{stream ? "关闭摄像头" : "启用本地预览"}</button>
    </div>
  );
}
