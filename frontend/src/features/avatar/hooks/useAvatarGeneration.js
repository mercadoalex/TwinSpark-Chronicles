import { useState } from 'react';
import { avatarService } from '../services/avatarService';

export function useAvatarGeneration() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedAvatar, setGeneratedAvatar] = useState(null);
  const [error, setError] = useState(null);

  const generateAvatar = async (photoBase64, metadata) => {
    setIsGenerating(true);
    setError(null);
    try {
      const avatar = await avatarService.generateAvatar({
        photo: photoBase64,
        name: metadata.name,
        gender: metadata.gender,
        spiritAnimal: metadata.spiritAnimal,
        toyName: metadata.toyName,
        style: 'child-friendly'
      });
      setGeneratedAvatar(avatar);
      return avatar;
    } catch (err) {
      console.error('Avatar generation error:', err);
      setError('No se pudo generar el avatar');
      throw err;
    } finally {
      setIsGenerating(false);
    }
  };

  const resetAvatar = () => {
    setGeneratedAvatar(null);
    setError(null);
  };

  return { isGenerating, generatedAvatar, error, generateAvatar, resetAvatar };
}
