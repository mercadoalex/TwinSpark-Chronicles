const handleSubmit = (e) => {
  e.preventDefault();
  
  // Asegúrate de que los datos se envían correctamente
  const profileData = {
    name: formData.name,
    gender: formData.gender,
    age: parseInt(formData.age),
    personality: formData.personality,      // ← Este es el personality TRAIT
    spiritAnimal: formData.spiritAnimal,    // ← Este es el spirit ANIMAL
    favoriteToy: formData.favoriteToy
  };
  
  console.log('ProfileForm submitting:', profileData); // Para debug
  onSubmit(profileData);
};