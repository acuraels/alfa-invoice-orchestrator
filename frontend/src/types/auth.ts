export type UserRole = 'admin' | 'factoring' | 'accounting' | 'taxation' | 'acquiring';

export type AuthUser = {
  id: number;
  username: string;
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
