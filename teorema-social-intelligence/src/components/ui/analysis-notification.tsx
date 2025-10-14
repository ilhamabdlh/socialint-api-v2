import React from 'react';
import { X } from 'lucide-react';

interface AnalysisNotificationProps {
  isOpen: boolean;
  onClose: () => void;
  campaignName: string;
  type: 'started' | 'completed' | 'failed';
}

export function AnalysisNotification({ isOpen, onClose, campaignName, type }: AnalysisNotificationProps) {
  console.log('🔧 AnalysisNotification rendered:', { isOpen, campaignName, type });
  
  if (!isOpen) return null;

  const getContent = () => {
    switch (type) {
      case 'started':
        return {
          title: 'Analysis Started',
          message: `Campaign "${campaignName}" analysis has been triggered and is now processing in the background. You will be notified when it's complete.`,
          buttonText: 'Close',
          buttonClass: 'bg-blue-500 hover:bg-blue-600 text-white'
        };
      case 'completed':
        return {
          title: 'Analysis Complete',
          message: `Campaign "${campaignName}" analysis has been completed successfully. The results are now ready for review.`,
          buttonText: 'Close',
          buttonClass: 'bg-green-500 hover:bg-green-600 text-white'
        };
      case 'failed':
        return {
          title: 'Analysis Failed',
          message: `Campaign "${campaignName}" analysis encountered an error. Please check the campaign settings and try again.`,
          buttonText: 'Close',
          buttonClass: 'bg-red-500 hover:bg-red-600 text-white'
        };
    }
  };

  const content = getContent();

  return (
    <div 
      className="fixed inset-0 bg-white bg-opacity-5 flex items-center justify-center z-50 p-4 pointer-events-auto"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          console.log('🔧 Background clicked');
          onClose();
        }
      }}
    >
      {/* White popup box */}
      <div 
        className="bg-white rounded-lg shadow-lg w-80 p-4 relative border border-gray-300 pointer-events-auto" 
        style={{ backgroundColor: 'white' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('🔧 X button clicked');
            onClose();
          }}
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-600 transition-colors cursor-pointer z-10 bg-transparent border-0 p-1"
          style={{ backgroundColor: 'transparent', border: 'none' }}
        >
          <X className="h-5 w-5" />
        </button>

        {/* Content */}
        <div className="text-center" style={{ color: 'black' }}>
          <h2 className="text-lg font-bold text-gray-900 mb-2" style={{ color: 'black' }}>{content.title}</h2>
          <p className="text-gray-700 text-xs leading-relaxed mb-4" style={{ color: 'black' }}>
            {content.message}
          </p>
          
          {/* Action button */}
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              console.log('🔧 Close button clicked');
              onClose();
            }}
            className="font-medium px-3 py-1.5 rounded-md shadow-sm hover:shadow-md transition-all duration-200 border-0 cursor-pointer text-xs"
            style={{ 
              backgroundColor: type === 'started' ? '#3b82f6' : type === 'completed' ? '#10b981' : '#ef4444',
              color: 'white',
              border: 'none',
              outline: 'none'
            }}
          >
            {content.buttonText}
          </button>
        </div>
      </div>
    </div>
  );
}
