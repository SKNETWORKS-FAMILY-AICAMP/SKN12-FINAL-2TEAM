"use client"

import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { supabase } from '@/lib/supabaseClient'
import QRCode from 'qrcode'

export default function VerifyOTP() {
  const router = useRouter()
  const [qrUrl, setQrUrl] = useState<string | null>(null)
  const [factorId, setFactorId] = useState<string | null>(null)
  const [challengeId, setChallengeId] = useState<string | null>(null)
  const [code, setCode] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const [loading, setLoading] = useState(false)

  // 로그인 세션이 없으면 접근 불가
  useEffect(() => {
    const checkSession = async () => {
      const { data } = await supabase.auth.getSession()
      if (!data.session) {
        router.replace('/login')
      }
    }
    checkSession()
  }, [router])

  // 1. 회원가입 후 TOTP 등록(시크릿 발급)
  useEffect(() => {
    const enrollTotp = async () => {
      setErrorMsg('')
      setLoading(true)
      const { data, error } = await supabase.auth.mfa.enroll({ factorType: 'totp' })
      if (error || !data) {
        setErrorMsg(error?.message || 'TOTP 등록 실패')
        setLoading(false)
        return
      }
      setFactorId(data.id)
      // otpauth_url을 QR코드로 변환
      const qr = await QRCode.toDataURL(data.totp.qr_code)
      setQrUrl(qr)
      setLoading(false)
    }
    enrollTotp()
  }, [])

  // 2. 사용자가 6자리 코드 입력 후 인증
  const handleVerify = async () => {
    setErrorMsg('')
    setLoading(true)
    if (!factorId) {
      setErrorMsg('인증 정보가 없습니다. 다시 시도해 주세요.')
      setLoading(false)
      return
    }
    // challenge 생성
    const { data: challengeData, error: challengeError } = await supabase.auth.mfa.challenge({ factorId })
    if (challengeError || !challengeData) {
      setErrorMsg(challengeError?.message || '챌린지 생성 실패')
      setLoading(false)
      return
    }
    setChallengeId(challengeData.id)
    // 코드 검증
    const { error: verifyError } = await supabase.auth.mfa.verify({
      factorId,
      challengeId: challengeData.id,
      code,
    })
    if (verifyError) {
      setErrorMsg('인증 코드가 올바르지 않습니다.')
      setLoading(false)
      return
    }
    // 인증 성공 시 대시보드로 이동
    setLoading(false)
    router.push('/dashboard')
  }

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
      <div className="w-full max-w-md bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold mb-4 text-center">2차 인증 (OTP) 등록</h2>
        <div className="mb-6 text-center text-gray-700">
          Google Authenticator 앱으로 QR코드를 스캔하고, 생성된 6자리 코드를 입력하세요.
        </div>
        <div className="w-full h-32 flex items-center justify-center mb-6">
          {qrUrl ? (
            <img src={qrUrl} alt="QR 코드" className="w-32 h-32" />
          ) : (
            <span className="text-gray-400">QR 코드 생성 중...</span>
          )}
        </div>
        <input
          type="text"
          placeholder="6자리 코드 입력"
          className="w-full h-12 px-4 mb-4 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={code}
          onChange={e => setCode(e.target.value)}
          maxLength={6}
        />
        {errorMsg && <div className="text-red-500 text-sm w-full text-center mb-2">{errorMsg}</div>}
        <button
          className="w-full h-12 bg-blue-600 text-white rounded font-semibold hover:bg-blue-700 transition"
          onClick={handleVerify}
          disabled={loading}
        >
          {loading ? '인증 중...' : '인증하기'}
        </button>
      </div>
    </div>
  )
} 