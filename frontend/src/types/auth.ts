export type UserRole = 'admin' | 'user';

export type AuthUser = {
  id: string | number;
  username: string;
  email?: string;
  full_name?: string;
  role: UserRole;
};

export type LoginRequest = {
  username: string;
  password: string;
};

export type LoginResponse = {
  refresh: string;
  access: string;
  user: AuthUser;
};

export type RefreshRequest = {
  refresh: string;
};

export type RefreshResponse = {
  access: string;
};
