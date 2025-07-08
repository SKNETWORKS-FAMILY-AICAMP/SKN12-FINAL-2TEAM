import { useRouter } from 'next/navigation'

export default function EmailVerifiedPage() {
  const router = useRouter()

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
      <div className="w-full max-w-md bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold mb-4 text-center">이메일 인증 완료</h2>
        <div className="mb-6 text-center text-gray-700">
          이메일 인증이 성공적으로 완료되었습니다.<br />
          추가 보안을 위해 OTP(2차 인증)를 설정하시겠습니까?
        </div>
        <div className="flex flex-col gap-4">
          <button
            className="w-full h-12 bg-blue-600 text-white rounded font-semibold hover:bg-blue-700 transition"
            onClick={() => router.push('/verify-otp')}
          >
            OTP(2차 인증) 설정하기
          </button>
          <button
            className="w-full h-12 bg-gray-200 text-gray-800 rounded font-semibold hover:bg-gray-300 transition"
            onClick={() => router.push('/dashboard')}
          >
            나중에 할게요 (바로 시작하기)
          </button>
        </div>
      </div>
    </div>
  )
} 