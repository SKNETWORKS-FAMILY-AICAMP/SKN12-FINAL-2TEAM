declare module 'trusted-types' {
  interface TrustedTypePolicy {
    createHTML(input: string): TrustedHTML;
    createScript(input: string): TrustedScript;
    createScriptURL(input: string): TrustedScriptURL;
  }

  interface TrustedHTML {}
  interface TrustedScript {}
  interface TrustedScriptURL {}

  interface TrustedTypePolicyFactory {
    createPolicy(
      name: string,
      rules?: {
        createHTML?: (input: string) => string;
        createScript?: (input: string) => string;
        createScriptURL?: (input: string) => string;
      }
    ): TrustedTypePolicy;
  }

  const trustedTypes: TrustedTypePolicyFactory;
  export = trustedTypes;
} 