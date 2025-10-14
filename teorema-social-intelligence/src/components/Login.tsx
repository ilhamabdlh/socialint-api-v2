import React, { useState } from "react";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { AlertCircle, Eye, EyeOff, Sparkles } from "lucide-react";
import logoSocialInt from "../../assets/logo_socialint.png";
import { credentials } from "../lib/credentials";

interface LoginProps {
  onLogin: (username: string, name: string) => void;
}

export function Login({ onLogin }: LoginProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    // Simulate loading delay untuk UX yang lebih baik
    await new Promise(resolve => setTimeout(resolve, 500));

    try {
      // Cek apakah user ada dalam credentials
      const user = credentials.users.find(
        (u) => u.username === username && u.password === password
      );

      if (user) {
        onLogin(user.username, user.name);
      } else {
        setError("Invalid username or password. Please try again.");
      }
    } catch (err) {
      setError("An error occurred during login. Please try again.");
      console.error("Login error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: '100vh', height: '100vh', overflow: 'hidden' }}>
      {/* Left Panel - Welcome Section */}
      <div style={{ 
        background: 'linear-gradient(135deg, #6b21a8 0%, #7c3aed 25%, #8b5cf6 50%, #6d28d9 75%, #581c87 100%)',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '48px',
        position: 'relative',
        overflow: 'hidden',
        color: 'white'
      }}>
        {/* Chevron/Zig-Zag Pattern */}
        <svg className="absolute inset-0 w-full h-full" style={{ opacity: 0.2 }} preserveAspectRatio="none">
          <defs>
            <linearGradient id="chevronGradient1" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" style={{ stopColor: '#a78bfa', stopOpacity: 0.8 }} />
              <stop offset="50%" style={{ stopColor: '#8b5cf6', stopOpacity: 0.6 }} />
              <stop offset="100%" style={{ stopColor: '#7c3aed', stopOpacity: 0.4 }} />
            </linearGradient>
            <linearGradient id="chevronGradient2" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" style={{ stopColor: '#c4b5fd', stopOpacity: 0.9 }} />
              <stop offset="50%" style={{ stopColor: '#a78bfa', stopOpacity: 0.7 }} />
              <stop offset="100%" style={{ stopColor: '#8b5cf6', stopOpacity: 0.5 }} />
            </linearGradient>
          </defs>
          
          {/* Chevron Pattern - Multiple Layers */}
          <path d="M 0,0 L 150,120 L 0,240 Z" fill="url(#chevronGradient1)" />
          <path d="M 150,120 L 300,0 L 450,120 L 300,240 Z" fill="url(#chevronGradient2)" />
          <path d="M 450,120 L 600,0 L 750,120 L 600,240 Z" fill="url(#chevronGradient1)" />
          <path d="M 750,120 L 900,0 L 1050,120 L 900,240 Z" fill="url(#chevronGradient2)" />
          
          <path d="M 0,240 L 150,360 L 0,480 Z" fill="url(#chevronGradient2)" />
          <path d="M 150,360 L 300,240 L 450,360 L 300,480 Z" fill="url(#chevronGradient1)" />
          <path d="M 450,360 L 600,240 L 750,360 L 600,480 Z" fill="url(#chevronGradient2)" />
          <path d="M 750,360 L 900,240 L 1050,360 L 900,480 Z" fill="url(#chevronGradient1)" />
          
          <path d="M 0,480 L 150,600 L 0,720 Z" fill="url(#chevronGradient1)" />
          <path d="M 150,600 L 300,480 L 450,600 L 300,720 Z" fill="url(#chevronGradient2)" />
          <path d="M 450,600 L 600,480 L 750,600 L 600,720 Z" fill="url(#chevronGradient1)" />
          <path d="M 750,600 L 900,480 L 1050,600 L 900,720 Z" fill="url(#chevronGradient2)" />
        </svg>
        
        {/* Subtle Lines Overlay */}
        <svg className="absolute inset-0 w-full h-full" style={{ opacity: 0.1 }}>
          <defs>
            <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style={{ stopColor: '#ffffff', stopOpacity: 0 }} />
              <stop offset="50%" style={{ stopColor: '#ffffff', stopOpacity: 0.8 }} />
              <stop offset="100%" style={{ stopColor: '#ffffff', stopOpacity: 0 }} />
            </linearGradient>
          </defs>
          <line x1="0" y1="15%" x2="100%" y2="15%" stroke="url(#lineGrad)" strokeWidth="3" />
          <line x1="0" y1="35%" x2="100%" y2="35%" stroke="url(#lineGrad)" strokeWidth="2" />
          <line x1="0" y1="55%" x2="100%" y2="55%" stroke="url(#lineGrad)" strokeWidth="3" />
          <line x1="0" y1="75%" x2="100%" y2="75%" stroke="url(#lineGrad)" strokeWidth="2" />
        </svg>
        
        {/* Decorative Elements - Multiple Layers */}
        <div className="absolute top-0 right-0 w-96 h-96 rounded-full" style={{ 
          background: 'radial-gradient(circle, rgba(167, 139, 250, 0.4) 0%, rgba(139, 92, 246, 0.2) 50%, transparent 70%)', 
          filter: 'blur(80px)',
          transform: 'translate(30%, -30%)'
        }}></div>
        
        <div className="absolute top-20 right-32 w-72 h-72 rounded-full" style={{ 
          background: 'radial-gradient(circle, rgba(236, 72, 153, 0.3) 0%, rgba(219, 39, 119, 0.15) 60%, transparent 80%)', 
          filter: 'blur(90px)',
          animation: 'float 8s ease-in-out infinite'
        }}></div>
        
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] rounded-full" style={{ 
          background: 'radial-gradient(circle, rgba(124, 58, 237, 0.5) 0%, rgba(109, 40, 217, 0.3) 40%, transparent 70%)', 
          filter: 'blur(100px)',
          transform: 'translate(-40%, 40%)'
        }}></div>
        
        <div className="absolute bottom-32 left-20 w-80 h-80 rounded-full" style={{ 
          background: 'radial-gradient(circle, rgba(59, 130, 246, 0.25) 0%, rgba(37, 99, 235, 0.1) 60%, transparent 80%)', 
          filter: 'blur(70px)',
          animation: 'float 10s ease-in-out infinite reverse'
        }}></div>
        
        {/* Logo Section */}
        <div style={{ position: 'relative', zIndex: 10, flex: '0 0 auto' }}>
          <Sparkles style={{ width: '64px', height: '64px' }} />
        </div>
        
        {/* Welcome Text - Centered Vertically */}
        <div style={{ 
          position: 'relative',
          zIndex: 10,
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'flex-start',
          paddingRight: '48px'
        }}>
          <h1 style={{ 
            fontSize: '56px', 
            fontWeight: '700', 
            lineHeight: '1.1', 
            marginBottom: '24px',
            color: 'white' 
          }}>
            Teorema Intelligence! 👋
          </h1>
          <p style={{ 
            fontSize: '18px', 
            color: '#e9d5ff', 
            lineHeight: '1.7',
            maxWidth: '540px'
          }}>
            Monitor and analyze your marketing campaigns in real-time. 
            Get deep insights from various social media platforms 
            in one unified dashboard.
          </p>
        </div>
        
        {/* Footer */}
        <div style={{ 
          position: 'relative',
          zIndex: 10,
          fontSize: '14px', 
          color: '#e9d5ff',
          flex: '0 0 auto'
        }}>
          © 2025 Teorema Intelligence. All rights reserved.
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div style={{ 
        backgroundColor: '#fafafa',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px',
        position: 'relative'
      }}>
        {/* Subtle gradient background on right panel */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'radial-gradient(circle at 50% 0%, rgba(139, 92, 246, 0.03) 0%, transparent 50%)',
          pointerEvents: 'none'
        }}></div>
        
        <div style={{ 
          width: '100%', 
          maxWidth: '480px',
          position: 'relative',
          zIndex: 10
        }}>
          {/* Header */}
          <div style={{ marginBottom: '48px' }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '12px',
              marginBottom: '32px'
            }}>
              <img 
                src={logoSocialInt} 
                alt="Social Intelligence Logo" 
                style={{ width: '40px', height: '40px', objectFit: 'contain' }}
              />
              <h2 style={{ 
                fontSize: '28px', 
                fontWeight: '700', 
                color: '#111827',
                margin: 0
              }}>
                Social Intelligence
              </h2>
            </div>
            <div>
              <h3 style={{ 
                fontSize: '28px', 
                fontWeight: '600', 
                color: '#1f2937', 
                marginBottom: '12px',
                margin: 0
              }}>
                Welcome Back!
              </h3>
              <p style={{ 
                fontSize: '15px', 
                color: '#6b7280', 
                lineHeight: '1.6',
                margin: 0
              }}>
                Enter your credentials to access your dashboard
              </p>
            </div>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Username Field */}
            <div>
              <Input
                id="username"
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                style={{ 
                  width: '100%', 
                  height: '50px', 
                  padding: '0 16px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '10px',
                  fontSize: '15px',
                  backgroundColor: '#ffffff',
                  boxShadow: 'none',
                  transition: 'all 0.2s',
                  outline: 'none'
                }}
                onFocus={(e: React.FocusEvent<HTMLInputElement>) => {
                  e.currentTarget.style.borderColor = '#8b5cf6';
                  e.currentTarget.style.boxShadow = '0 0 0 3px rgba(139, 92, 246, 0.08)';
                }}
                onBlur={(e: React.FocusEvent<HTMLInputElement>) => {
                  e.currentTarget.style.borderColor = '#e5e7eb';
                  e.currentTarget.style.boxShadow = 'none';
                }}
                required
                disabled={isLoading}
              />
            </div>

            {/* Password Field */}
            <div style={{ position: 'relative' }}>
              <Input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ 
                  width: '100%', 
                  height: '50px', 
                  padding: '0 48px 0 16px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '10px',
                  fontSize: '15px',
                  backgroundColor: '#ffffff',
                  boxShadow: 'none',
                  transition: 'all 0.2s',
                  outline: 'none'
                }}
                onFocus={(e: React.FocusEvent<HTMLInputElement>) => {
                  e.currentTarget.style.borderColor = '#8b5cf6';
                  e.currentTarget.style.boxShadow = '0 0 0 3px rgba(139, 92, 246, 0.08)';
                }}
                onBlur={(e: React.FocusEvent<HTMLInputElement>) => {
                  e.currentTarget.style.borderColor = '#e5e7eb';
                  e.currentTarget.style.boxShadow = 'none';
                }}
                required
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '16px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: '#9ca3af',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer'
                }}
                tabIndex={-1}
              >
                {showPassword ? (
                  <EyeOff style={{ width: '20px', height: '20px' }} />
                ) : (
                  <Eye style={{ width: '20px', height: '20px' }} />
                )}
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '8px', 
                padding: '12px', 
                backgroundColor: '#fef2f2', 
                border: '1px solid #fecaca',
                borderRadius: '8px',
                color: '#b91c1c',
                fontSize: '14px'
              }}>
                <AlertCircle style={{ width: '16px', height: '16px', flexShrink: 0 }} />
                <span>{error}</span>
              </div>
            )}

            {/* Submit Button */}
            <Button 
              type="submit" 
              style={{
                width: '100%',
                height: '54px',
                backgroundColor: isLoading ? '#4b5563' : '#111827',
                color: '#ffffff',
                fontWeight: '600',
                fontSize: '16px',
                borderRadius: '10px',
                border: 'none',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                transition: 'all 0.15s ease',
                boxShadow: 'none',
                marginTop: '8px'
              }}
              disabled={isLoading}
              onMouseEnter={(e: React.MouseEvent<HTMLButtonElement>) => {
                if (!isLoading) {
                  e.currentTarget.style.backgroundColor = '#1f2937';
                  e.currentTarget.style.transform = 'translateY(-1px)';
                }
              }}
              onMouseLeave={(e: React.MouseEvent<HTMLButtonElement>) => {
                if (!isLoading) {
                  e.currentTarget.style.backgroundColor = '#111827';
                  e.currentTarget.style.transform = 'translateY(0)';
                }
              }}
            >
              {isLoading ? "Processing..." : "Login Now"}
            </Button>

            {/* Demo Info */}
            <div style={{ 
              padding: '20px', 
              backgroundColor: '#faf5ff', 
              border: '1px solid #e9d5ff',
              borderRadius: '10px',
              marginTop: '8px'
            }}>
              <p style={{ 
                fontSize: '13px', 
                color: '#581c87', 
                fontWeight: '600', 
                textAlign: 'center', 
                marginBottom: '12px',
                margin: 0,
                paddingBottom: '12px'
              }}>
                Demo credentials for testing:
              </p>
              <div style={{ fontSize: '13px', color: '#6b21a8', textAlign: 'center' }}>
                <p style={{ margin: 0, marginBottom: '6px' }}>
                  <strong>Admin:</strong> admin / admin123
                </p>
                <p style={{ margin: 0 }}>
                  <strong>User:</strong> user / user123
                </p>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

