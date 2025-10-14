// Credentials untuk demo login
export interface User {
  username: string;
  password: string;
  name: string;
  role: 'admin' | 'user';
}

export const credentials = {
  users: [
    {
      username: 'admin',
      password: 'admin123',
      name: 'Administrator',
      role: 'admin' as const
    },
    {
      username: 'user',
      password: 'user123',
      name: 'User',
      role: 'user' as const
    }
  ]
};

