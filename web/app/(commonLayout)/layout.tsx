import React from 'react'
import type { ReactNode } from 'react'
import SwrInitor from '@/app/components/swr-initor'
import { AppContextProvider } from '@/context/app-context'
import HeaderWrapper from '@/app/components/header/HeaderWrapper'
import Header from '@/app/components/header'
import { EventEmitterContextProvider } from '@/context/event-emitter'
import { ProviderContextProvider } from '@/context/provider-context'

const Layout = ({ children }: { children: ReactNode }) => {
  return (
    <>
      {/* dqf <GA gaType={GaType.admin} /> */}
      <SwrInitor>
        <AppContextProvider>
          <EventEmitterContextProvider>
            <ProviderContextProvider>
              <HeaderWrapper>
                <Header />
              </HeaderWrapper>
              {children}
            </ProviderContextProvider>
          </EventEmitterContextProvider>
        </AppContextProvider>
      </SwrInitor>
    </>
  )
}

export const metadata = {
  title: 'CC-Bots',
}

export default Layout
