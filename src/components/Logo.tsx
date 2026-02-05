import Image from "next/image";

interface LogoProps {
  size?: "sm" | "md" | "lg";
  showText?: boolean;
  className?: string;
}

const sizes = {
  sm: { icon: 32, text: "text-lg" },
  md: { icon: 40, text: "text-xl" },
  lg: { icon: 64, text: "text-3xl" },
};

export function Logo({ size = "md", showText = true, className = "" }: LogoProps) {
  const { icon, text } = sizes[size];

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* If logo.png exists in public folder, use it */}
      <div className="relative" style={{ width: icon, height: icon }}>
        <Image
          src="/logo.png"
          alt="Portal IQ"
          width={icon}
          height={icon}
          className="object-contain"
          onError={(e) => {
            // Fallback to SVG if PNG not found
            e.currentTarget.style.display = 'none';
            e.currentTarget.nextElementSibling?.classList.remove('hidden');
          }}
        />
        {/* Fallback SVG */}
        <svg
          viewBox="0 0 100 100"
          className="hidden absolute inset-0"
          style={{ width: icon, height: icon }}
        >
          {/* Arch/Portal shape */}
          <path
            d="M15 95 L15 40 Q15 10 50 10 Q85 10 85 40 L85 95"
            fill="none"
            stroke="#D4AF37"
            strokeWidth="6"
          />
          {/* Compass circle */}
          <circle cx="50" cy="52" r="30" fill="none" stroke="#D4AF37" strokeWidth="4" />
          {/* Compass points */}
          <path
            d="M50 25 L53 45 L50 52 L47 45 Z M50 79 L53 59 L50 52 L47 59 Z M23 52 L43 49 L50 52 L43 55 Z M77 52 L57 49 L50 52 L57 55 Z"
            fill="#D4AF37"
          />
          {/* Diagonal points */}
          <path
            d="M30 32 L45 47 L50 52 L47 45 Z M70 32 L55 47 L50 52 L53 45 Z M30 72 L45 57 L50 52 L47 55 Z M70 72 L55 57 L50 52 L53 55 Z"
            fill="#D4AF37"
            opacity="0.6"
          />
          {/* Helmet shape */}
          <ellipse cx="50" cy="52" rx="12" ry="10" fill="#0f1a2e" />
          <path
            d="M40 52 Q40 42 50 42 Q60 42 60 52 Q60 58 50 60 Q40 58 40 52"
            fill="#D4AF37"
          />
          <rect x="55" y="48" width="8" height="3" fill="#0f1a2e" rx="1" />
        </svg>
      </div>
      {showText && (
        <span className={`font-bold text-white ${text}`}>
          Portal IQ
        </span>
      )}
    </div>
  );
}

// Inline SVG version for when we don't need the image
export function LogoIcon({ size = 40, className = "" }: { size?: number; className?: string }) {
  return (
    <svg
      viewBox="0 0 100 100"
      className={className}
      style={{ width: size, height: size }}
    >
      {/* Arch/Portal shape */}
      <path
        d="M15 95 L15 40 Q15 10 50 10 Q85 10 85 40 L85 95"
        fill="none"
        stroke="#D4AF37"
        strokeWidth="6"
      />
      {/* Compass circle */}
      <circle cx="50" cy="52" r="30" fill="none" stroke="#D4AF37" strokeWidth="4" />
      {/* Compass points - main */}
      <polygon points="50,22 54,45 50,52 46,45" fill="#D4AF37" />
      <polygon points="50,82 54,59 50,52 46,59" fill="#D4AF37" />
      <polygon points="18,52 41,48 50,52 41,56" fill="#D4AF37" />
      <polygon points="82,52 59,48 50,52 59,56" fill="#D4AF37" />
      {/* Diagonal points */}
      <polygon points="28,30 44,46 50,52 46,46" fill="#D4AF37" opacity="0.7" />
      <polygon points="72,30 56,46 50,52 54,46" fill="#D4AF37" opacity="0.7" />
      <polygon points="28,74 44,58 50,52 46,58" fill="#D4AF37" opacity="0.7" />
      <polygon points="72,74 56,58 50,52 54,58" fill="#D4AF37" opacity="0.7" />
      {/* Helmet */}
      <circle cx="50" cy="52" r="11" fill="#1a2744" />
      <path
        d="M41 54 Q41 44 50 44 Q59 44 59 54 Q59 60 50 61 Q41 60 41 54"
        fill="#D4AF37"
      />
      <rect x="56" y="50" width="6" height="2.5" fill="#1a2744" rx="1" />
    </svg>
  );
}
