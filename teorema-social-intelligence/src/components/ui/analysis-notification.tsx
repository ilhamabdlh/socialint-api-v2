import React from 'react';
import { Loader2 } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './dialog';
import { Label } from './label';
import { Badge } from './badge';
import { Button } from './button';

interface AnalysisNotificationProps {
  isOpen: boolean;
  onClose: () => void;
  campaignName: string;
  type: 'started' | 'completed' | 'failed';
  analysisId?: string;
  platforms?: string[];
  keywords?: string[];
  estimatedCompletion?: string;
}

export function AnalysisNotification({ 
  isOpen, 
  onClose, 
  campaignName, 
  type, 
  analysisId, 
  platforms, 
  keywords, 
  estimatedCompletion 
}: AnalysisNotificationProps) {
  console.log('🔧 AnalysisNotification rendered:', { isOpen, campaignName, type });
  
  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => {
      if (!open) {
        onClose();
      }
    }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold">
            {type === 'started' ? 'Analysis Started' : type === 'completed' ? 'Analysis Completed' : 'Analysis Failed'}
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          {type === 'started' ? (
            <>
              <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex-shrink-0">
                  <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-blue-900">
                    Campaign analysis for <span className="font-semibold">{campaignName}</span> is now running in the background.
                  </p>
                  <p className="text-xs text-blue-700 mt-1">
                    Estimated completion: {estimatedCompletion || '5-10 minutes'}
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                {analysisId && (
                  <div>
                    <Label className="text-sm font-medium text-gray-700">Analysis ID</Label>
                    <p className="text-sm text-gray-600 font-mono bg-gray-50 p-2 rounded mt-1">
                      {analysisId}
                    </p>
                  </div>
                )}

                {platforms && platforms.length > 0 && (
                  <div>
                    <Label className="text-sm font-medium text-gray-700">Platforms</Label>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {platforms.map((platform) => (
                        <Badge key={platform} variant="outline" className="capitalize">
                          {platform}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {keywords && keywords.length > 0 && (
                  <div>
                    <Label className="text-sm font-medium text-gray-700">Keywords</Label>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {keywords.map((keyword, index) => (
                        <Badge key={index} variant="secondary">
                          {keyword}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-xs text-gray-600">
                  You can continue working while the analysis runs. We'll update the results automatically when it's complete.
                </p>
              </div>
            </>
          ) : type === 'completed' ? (
            <>
              <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg border border-green-200">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-900">
                    Campaign analysis for <span className="font-semibold">{campaignName}</span> has been completed successfully.
                  </p>
                  <p className="text-xs text-green-700 mt-1">
                    The results are now ready for review.
                  </p>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center gap-3 p-4 bg-red-50 rounded-lg border border-red-200">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-900">
                    Campaign analysis for <span className="font-semibold">{campaignName}</span> encountered an error.
                  </p>
                  <p className="text-xs text-red-700 mt-1">
                    Please check the campaign settings and try again.
                  </p>
                </div>
              </div>
            </>
          )}
        </div>

        <div className="flex justify-end pt-4">
          <Button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              console.log('🔧 Close button clicked');
              onClose();
            }}
            className="px-6 py-2"
          >
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}