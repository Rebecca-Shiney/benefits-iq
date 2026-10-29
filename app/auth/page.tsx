"use client";

import { broadcastResponseToMainFrame } from "@azure/msal-browser/redirect-bridge";
import { useEffect, useState } from "react";

export default function AuthenticationReturn() {
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    void broadcastResponseToMainFrame().catch(() => {
      console.error("Microsoft Entra authentication response could not be relayed.");
      setFailed(true);
    });
  }, []);
  return <main><p role={failed ? "alert" : "status"}>{failed
    ? "Sign-in could not finish. Close this window and retry from Benefits IQ."
    : "Completing Microsoft Entra sign-in. This window will close automatically."}</p></main>;
}
