const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class AvatarService {
  async generateAvatar({ photo, name, gender, spiritAnimal, toyName, style }) {
    try {
      const url = `${API_URL}/api/avatar/generate`;
      
      console.log('🔵 Calling avatar API:', url);
      
      const response = await fetch(url, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          photo_base64: photo,
          metadata: { 
            name, 
            gender, 
            spirit_animal: spiritAnimal, 
            toy_name: toyName, 
            style: style || 'child-friendly' 
          }
        })
      });

      console.log('🔵 Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ API Error:', errorText);
        throw new Error(`Avatar generation failed: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ Avatar generated:', data);
      
      return { 
        avatarUrl: data.avatar_url, 
        avatarBase64: data.avatar_base64, 
        metadata: data.metadata 
      };
      
    } catch (error) {
      console.error('❌ avatarService.generateAvatar error:', error);
      throw error;
    }
  }

  async getAvatar(avatarId) {
    const url = `${API_URL}/api/avatar/${avatarId}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Avatar not found');
    return await response.json();
  }
}

export const avatarService = new AvatarService();
