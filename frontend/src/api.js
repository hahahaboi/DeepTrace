const API_BASE_URL = "http://localhost:8000";

export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/`);
    if (!res.ok) return false;
    const data = await res.json();
    return data.status === "healthy";
  } catch {
    return false;
  }
}

export async function fetchClusters() {
  try {
    const res = await fetch(`${API_BASE_URL}/analytics/clusters`);
    if (!res.ok) throw new Error("Failed to fetch clusters");
    return await res.json();
  } catch (err) {
    console.error("fetchClusters error:", err);
    return [];
  }
}

export async function fetchClusterDetail(clusterId) {
  try {
    const res = await fetch(`${API_BASE_URL}/analytics/clusters/${clusterId}`);
    if (!res.ok) throw new Error(`Failed to fetch cluster ${clusterId}`);
    return await res.json();
  } catch (err) {
    console.error(`fetchClusterDetail error:`, err);
    return null;
  }
}

export async function fetchPatterns(limit = 10) {
  try {
    const res = await fetch(`${API_BASE_URL}/analytics/patterns?limit=${limit}`);
    if (!res.ok) throw new Error("Failed to fetch patterns");
    return await res.json();
  } catch (err) {
    console.error("fetchPatterns error:", err);
    return [];
  }
}

export async function fetchFlakyTests(minRuns = 2, threshold = 0.2) {
  try {
    const res = await fetch(`${API_BASE_URL}/analytics/flaky-tests?min_runs=${minRuns}&threshold=${threshold}`);
    if (!res.ok) throw new Error("Failed to fetch flaky tests");
    return await res.json();
  } catch (err) {
    console.error("fetchFlakyTests error:", err);
    return [];
  }
}

export async function sendMockWebhook(payloadObj, secret = "deeptrace_secret_123") {
  try {
    // Generate signature locally using SubtleCrypto in browser
    const encoder = new TextEncoder();
    const payloadStr = JSON.stringify(payloadObj);
    const keyData = encoder.encode(secret);
    const msgData = encoder.encode(payloadStr);

    const cryptoKey = await window.crypto.subtle.importKey(
      "raw",
      keyData,
      { name: "HMAC", hash: { name: "SHA-256" } },
      false,
      ["sign"]
    );
    const signatureBuffer = await window.crypto.subtle.sign("HMAC", cryptoKey, msgData);
    const hashArray = Array.from(new Uint8Array(signatureBuffer));
    const hexSig = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    const signatureHeader = `sha256=${hexSig}`;

    const res = await fetch(`${API_BASE_URL}/webhooks/github`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-GitHub-Event": "workflow_run",
        "X-Hub-Signature-256": signatureHeader
      },
      body: payloadStr
    });

    const data = await res.json();
    return { ok: res.ok, status: res.status, data };
  } catch (err) {
    return { ok: false, status: 500, data: { error: err.message } };
  }
}
