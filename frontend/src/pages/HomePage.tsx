/**
 * HomePage with BackgroundPaths component
 * Beautiful landing page for OCR PDF Search System
 */
import { useNavigate } from 'react-router-dom';
import { BackgroundPaths } from '../components/ui/background-paths';

export default function HomePage() {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate('/search');
  };

  return (
    <BackgroundPaths 
      title="OCR PDF Search" 
      onButtonClick={handleGetStarted}
    />
  );
}

