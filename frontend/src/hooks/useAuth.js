import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { auth } from '../services/api'

export function useAuth() {
  const queryClient = useQueryClient()
  
  const { data: authStatus, isLoading } = useQuery({
    queryKey: ['auth'],
    queryFn: auth.status,
    retry: false,
  })

  const loginMutation = useMutation({
    mutationFn: ({ username, password }) => auth.login(username, password),
    onSuccess: () => {
      queryClient.invalidateQueries(['auth'])
    },
  })

  const logoutMutation = useMutation({
    mutationFn: auth.logout,
    onSuccess: () => {
      queryClient.invalidateQueries(['auth'])
    },
  })

  return {
    isAuthenticated: authStatus?.authenticated || false,
    isLoading,
    login: (username, password) => loginMutation.mutate({ username, password }),
    logout: logoutMutation.mutate,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error?.message,
  }
}