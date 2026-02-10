"use client";

import { useState, useEffect } from "react";
import { useSubscriptionTier } from "@/stores/auth-store";

const tierLabels: Record<string, string> = {
  free: "Free Plan",
  pro: "Pro Plan",
  enterprise: "Enterprise Plan",
};

export default function SettingsPage() {
  const subscriptionTier = useSubscriptionTier();
  const [settings, setSettings] = useState({
    emailAlerts: true,
    portalAlerts: true,
    nilThreshold: 5000,
    preferredConference: "all",
  });

  useEffect(() => {
    const saved = localStorage.getItem("portaliq_settings");
    if (saved) {
      try {
        setSettings(JSON.parse(saved));
      } catch {
        console.error("Failed to parse settings");
      }
    }
  }, []);

  const updateSetting = (key: string, value: boolean | number | string) => {
    const updated = { ...settings, [key]: value };
    setSettings(updated);
    localStorage.setItem("portaliq_settings", JSON.stringify(updated));
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-2">Settings</h1>
      <p className="text-gray-400 mb-6">Manage your Portal IQ preferences</p>

      {/* Notification Settings */}
      <div className="bg-[#1a2744] rounded-xl p-6 mb-6">
        <h2 className="text-lg font-bold text-white mb-4">Notifications</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-medium">Email Alerts</p>
              <p className="text-gray-400 text-sm">Receive weekly portal digest</p>
            </div>
            <button
              onClick={() => updateSetting("emailAlerts", !settings.emailAlerts)}
              className={`w-12 h-6 rounded-full transition ${
                settings.emailAlerts ? "bg-[#D4AF37]" : "bg-[#243354]"
              }`}
            >
              <div
                className={`w-5 h-5 rounded-full bg-white shadow transition transform ${
                  settings.emailAlerts ? "translate-x-6" : "translate-x-0.5"
                }`}
              />
            </button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-medium">Portal Activity Alerts</p>
              <p className="text-gray-400 text-sm">Get notified when watchlist players commit</p>
            </div>
            <button
              onClick={() => updateSetting("portalAlerts", !settings.portalAlerts)}
              className={`w-12 h-6 rounded-full transition ${
                settings.portalAlerts ? "bg-[#D4AF37]" : "bg-[#243354]"
              }`}
            >
              <div
                className={`w-5 h-5 rounded-full bg-white shadow transition transform ${
                  settings.portalAlerts ? "translate-x-6" : "translate-x-0.5"
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* NIL Settings */}
      <div className="bg-[#1a2744] rounded-xl p-6 mb-6">
        <h2 className="text-lg font-bold text-white mb-4">NIL Preferences</h2>
        <div className="space-y-4">
          <div>
            <label className="text-white font-medium block mb-2">
              Minimum NIL Value Alert Threshold
            </label>
            <select
              value={settings.nilThreshold}
              onChange={(e) => updateSetting("nilThreshold", Number(e.target.value))}
              className="w-full bg-[#243354] border border-[#3a4d6e] rounded-lg px-4 py-2 text-white focus:outline-none focus:border-[#D4AF37]"
            >
              <option value={1000}>$1,000+</option>
              <option value={5000}>$5,000+</option>
              <option value={10000}>$10,000+</option>
              <option value={25000}>$25,000+ (Moderate)</option>
              <option value={100000}>$100,000+ (Solid)</option>
              <option value={500000}>$500,000+ (Premium)</option>
            </select>
          </div>
          <div>
            <label className="text-white font-medium block mb-2">Preferred Conference</label>
            <select
              value={settings.preferredConference}
              onChange={(e) => updateSetting("preferredConference", e.target.value)}
              className="w-full bg-[#243354] border border-[#3a4d6e] rounded-lg px-4 py-2 text-white focus:outline-none focus:border-[#D4AF37]"
            >
              <option value="all">All Conferences</option>
              <option value="sec">SEC</option>
              <option value="bigten">Big Ten</option>
              <option value="acc">ACC</option>
              <option value="big12">Big 12</option>
            </select>
          </div>
        </div>
      </div>

      {/* Account */}
      <div className="bg-[#1a2744] rounded-xl p-6">
        <h2 className="text-lg font-bold text-white mb-4">Account</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between py-3 border-b border-[#243354]">
            <div>
              <p className="text-white font-medium">Subscription</p>
              <p className="text-[#D4AF37] text-sm">{tierLabels[subscriptionTier] || "Free Plan"}</p>
            </div>
            <a
              href="/pricing"
              className="text-gray-400 hover:text-white text-sm"
            >
              Manage
            </a>
          </div>
          <div className="flex items-center justify-between py-3">
            <div>
              <p className="text-white font-medium">Data Export</p>
              <p className="text-gray-400 text-sm">Download your data</p>
            </div>
            <button className="bg-[#243354] text-white px-4 py-2 rounded-lg hover:bg-[#2a3d5e] text-sm">
              Export All
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
