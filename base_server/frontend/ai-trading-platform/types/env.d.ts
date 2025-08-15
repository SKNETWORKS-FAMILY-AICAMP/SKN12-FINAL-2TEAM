declare global {
  namespace NodeJS {
    interface ProcessEnv {
      HOSTNAME: string;
      NEXT_PUBLIC_HOSTNAME: string;
      NEXT_PUBLIC_API_BASE_URL: string;
      NEXT_PUBLIC_DEV_HOST: string;
      NEXT_PUBLIC_DEV_PORT: string;
    }
  }
}

export {};

