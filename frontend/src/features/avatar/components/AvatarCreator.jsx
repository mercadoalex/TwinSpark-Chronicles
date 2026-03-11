import React, { useState } from 'react';
import AvatarCapture from './AvatarCapture';
import AvatarPreview from './AvatarPreview';
import { useAvatarGeneration } from '../hooks/useAvatarGeneration';

export default function AvatarCreator({ childMetadata, onComplete, onSkip }) {
  const [step, setStep] = useState('capture');
  const [capturedPhoto, setCapturedPhoto] = useState(null);
  const { isGenerating, generatedAvatar, error, generateAvatar, resetAvatar } = useAvatarGeneration();

  const handleCapture = async (photoBase64) => {
    setCapturedPhoto(photoBase64);
    setStep('preview');
    try {
      await generateAvatar(photoBase64, childMetadata);
    } catch (err) {
      console.error('Error generating avatar:', err);
    }
  };

  const handleRetake = () => {
    setCapturedPhoto(null);
    resetAvatar();
    setStep('capture');
  };

  const handleConfirm = () => {
    onComplete({ photo: capturedPhoto, avatar: generatedAvatar });
  };

  if (step === 'capture') {
    return <AvatarCapture onCapture={handleCapture} onCancel={onSkip} />;
  }

  return (
    <AvatarPreview
      isGenerating={isGenerating}
      avatarUrl={generatedAvatar?.avatarUrl}
      avatarBase64={generatedAvatar?.avatarBase64 || capturedPhoto}
      childName={childMetadata.name}
      onRetake={handleRetake}
      onConfirm={handleConfirm}
    />
  );
}
