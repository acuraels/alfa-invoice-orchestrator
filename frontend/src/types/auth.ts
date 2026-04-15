export type UserRole = 'admin' | 'user';

export type AuthDepartment = {
  id: string | number;
  name: string;
};

export type AuthUser = {
  id: string | number;
  login: string;
  full_name: string;
  role: UserRole;
  departments: AuthDepartment[];
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
