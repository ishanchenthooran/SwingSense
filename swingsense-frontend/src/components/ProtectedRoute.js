import React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  if (!user) {
    return null; // or a loading spinner
  }

  return children;
};

export default ProtectedRoute;
