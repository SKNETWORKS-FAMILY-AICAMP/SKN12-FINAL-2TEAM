export default function EmailVerificationPage() {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
      <div className="w-full max-w-md bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold mb-4 text-center">이메일 인증 안내</h2>
        <div className="mb-6 text-center text-gray-700">
          회원가입이 완료되었습니다.<br />
          이메일로 전송된 인증 링크를 클릭해 인증을 완료해 주세요.<br />
          인증 후 로그인하시면 2차 인증(OTP) 등록이 진행됩니다.
        </div>
      </div>
    </div>
  )
} 